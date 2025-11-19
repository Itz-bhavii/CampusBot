"""
Document parsing module for CampusBot ingestion pipeline.
Extracts text, tables, and metadata from various document formats.

SUPPORTED FORMATS:
- PDF (application/pdf)
- Plain text (text/plain)
- Word documents (DOCX - application/vnd.openxmlformats-officedocument.wordprocessingml.document)

PARSING STRATEGY:
1. Detect file type using MIME type detection
2. Extract structured elements (titles, paragraphs, lists, tables)
3. Preserve document structure and metadata
4. Split large text into smaller chunks for better AI retrieval
5. Return text chunks with metadata for vector database storage

OUTPUT FORMAT:
Returns two parallel lists:
- documents: list of text chunks (strings)
- metadata: list of dicts with document_id, heading, page number, etc.

These are stored in ChromaDB for semantic search by the query service.
"""

import re
import magic  # MIME type detection library
import tabula  # PDF table extraction library
import logging.config
from datetime import datetime
from unstructured.partition.pdf import partition_pdf  # PDF parsing
from unstructured.partition.text import partition_text  # Plain text parsing
from unstructured.partition.docx import partition_docx  # Word document parsing
from campusbot.common.campus_logger import LOGGING_CONFIG
from langchain_text_splitters import RecursiveCharacterTextSplitter  # Intelligent text chunking
from unstructured.documents.elements import Title,NarrativeText,ListItem,Table  # Document element types

# Configure logging using centralized config
logging.config.dictConfig(LOGGING_CONFIG)
logger = logging.getLogger(__name__)


def sanitizeText(text: str) -> str:
    """
    Cleans and normalizes extracted text for better AI understanding.
    
    CLEANING OPERATIONS:
    1. Fix hyphenated words split across lines
       Example: "docu-\nment" → "document"
    
    2. Remove page number patterns
       Example: "5 of 20" → ""
       Prevents irrelevant page numbers from affecting search
    
    3. Normalize whitespace
       - Multiple spaces → single space
       - Multiple newlines → single space
       - Leading/trailing whitespace removed
    
    WHY SANITIZE:
    - Improves embedding quality (cleaner text = better vectors)
    - Reduces noise in search results
    - Makes chunks more readable when displayed to users
    
    Args:
        text: Raw text extracted from document
    
    Returns:
        Cleaned text ready for embedding and storage
    """
    # Fix words broken across lines (remove hyphen + newline)
    text = re.sub(r'-\n', '', text)
    
    # Remove page numbers, headers, footers
    text = re.sub(r'\d+ of \d+', '', text)
    
    # Collapse all whitespace into single spaces
    text = re.sub(r'\s+', ' ', text).strip()
    
    return text

def parseFile(fileNameWithPath:str,filename:str,documentId:str):
    """
    Main parsing function - extracts text and metadata from uploaded documents.
    
    COMPLETE PARSING FLOW:
    
    1. MIME TYPE DETECTION:
       - Uses libmagic to detect actual file type (not just extension)
       - Prevents security issues from fake extensions
       - Example: file.txt might actually be a PDF
    
    2. FORMAT-SPECIFIC PARSING:
       - PDF: uses "hi_res" strategy for better quality
         * Infers table structure (preserves table data)
         * Extracts text with layout awareness
       - Text: simple line-by-line parsing
       - DOCX: parses Word document structure
    
    3. ELEMENT EXTRACTION:
       Document is parsed into structured elements:
       - Title: headings, section headers
       - NarrativeText: paragraphs, body text
       - ListItem: bullet points, numbered lists
       - Table: tabular data
    
    4. CHUNKING STRATEGY:
       Small chunks (<1000 chars): stored as-is
       Large chunks (≥1000 chars): split into smaller pieces
       
       WHY CHUNK:
       - AI embeddings work better on focused text
       - Smaller chunks = more precise retrieval
       - User gets exactly relevant paragraph, not whole page
    
    5. METADATA TRACKING:
       Each chunk stores:
       - document_id: hash of source file (for tracking)
       - source_heading: which section it came from (context)
       - filename: original file name (user reference)
       - page_no: which page (for citation)
       - element_type: Title, NarrativeText, etc. (structure info)
       - chunk_index: order within document (for reconstruction)
       - upload_date: when added (for filtering)
    
    6. TABLE HANDLING:
       - Tables detected on specific pages
       - Extracted using tabula library
       - Converted to Markdown format
       - Markdown preserves structure while being searchable
       Example:
         | Course | Credits |
         | CS101  | 3       |
         | CS201  | 4       |
    
    USAGE IN PIPELINE:
    worker.py downloads file → parseFile() extracts text → storeText() saves to ChromaDB
    
    Args:
        fileNameWithPath: Full path to downloaded file (/tmp/xyz/document.pdf)
        filename: Original filename for metadata (document.pdf)
        documentId: SHA-256 hash identifying this document
    
    Returns:
        Tuple of (documents, metadata):
        - documents: List of text chunks (strings)
        - metadata: List of dicts with metadata for each chunk
    
    Raises:
        Exception: If file format not supported
    """
    print("successfully entered parsed")
    
    # Step 1: Detect actual MIME type (more reliable than file extension)
    mimeType = magic.from_file(fileNameWithPath,mime=True)
    
    # Step 2: Parse document based on detected type
    if(mimeType == 'application/pdf'):
        # PDF parsing with high-resolution strategy for better quality
        # infer_table_structure=True enables table detection and extraction
        doc = partition_pdf(fileNameWithPath,strategy="hi_res",infer_table_structure=True)
        logger.info("Opened The Pdf File")
        
    elif(mimeType == 'text/plain'):
        # Simple text file parsing
        doc = partition_text(fileNameWithPath)
        logger.info("Opened The Text File")
        
    elif(mimeType == 'application/vnd.openxmlformats-officedocument.wordprocessingml.document'):
        # Microsoft Word document parsing
        doc = partition_docx(fileNameWithPath)
        
    else:
        # Unsupported format - reject to prevent errors
        logger.error("Invalid File Format")
        raise Exception("Invalid File Format")
    
    # Step 3: Initialize text splitter for large chunks
    # RecursiveCharacterTextSplitter intelligently splits on natural boundaries
    textSplitter = RecursiveCharacterTextSplitter(
        chunk_size = 1000,         # Target size per chunk
        chunk_overlap = 200,        # Overlap between chunks (preserves context)
        separators=["\n\n","\n"," ",""]  # Split on paragraphs, then lines, then words
    )

    # Step 4: Prepare storage containers
    documentsToAdd = []  # List of text chunks
    metadataToAdd = []   # Corresponding metadata for each chunk
    currentHeading = "General"  # Track current section heading
    chunkIndex = 0  # Sequential index for chunks
    
    # Step 5: Process each element in the parsed document
    for page in doc:
        # Extract page number from metadata (0 if not available)
        pageNo = page.metadata.page_number
        if not pageNo:
            pageNo = 0

        # Handle Title elements - these become section headings
        if isinstance(page,Title):
            # Update current heading context
            # All following chunks will be tagged with this heading
            currentHeading = page.text.strip()

        # Handle text content (paragraphs and list items)
        elif isinstance(page,NarrativeText) or isinstance(page,ListItem):
            # Small chunks: store directly without further splitting
            if len(page.text) < 1000 :
                documentsToAdd.append(sanitizeText(page.text.strip()))
                metadataToAdd.append({
                    "document_id" : documentId,
                    "source_heading" : currentHeading,  # Which section this came from
                    "filename" : filename,
                    "page_no" : pageNo,
                    "element_type" : type(page).__name__,  # "NarrativeText" or "ListItem"
                    "chunk_index" : chunkIndex,
                    "upload_date" : datetime.now().strftime("%Y-%m-%d")
                })
                chunkIndex += 1
                
            # Large chunks: split into smaller pieces
            else :
                # RecursiveCharacterTextSplitter intelligently splits on:
                # 1. Paragraph breaks (\n\n)
                # 2. Line breaks (\n)
                # 3. Spaces ( )
                # Preserves context with 200-char overlap between chunks
                subChunks = textSplitter.split_text(page.text)
                
                # Store each sub-chunk with metadata
                for chunk in subChunks:
                    documentsToAdd.append(sanitizeText(chunk))
                    metadataToAdd.append({
                        "document_id" : documentId,
                        "source_heading" : currentHeading,
                        "filename" : filename,
                        "page_no" : pageNo,
                        "element_type" : type(page).__name__,
                        "chunk_index" : chunkIndex,
                        "upload_date" : datetime.now().strftime("%Y-%m-%d")
                    })
                    chunkIndex += 1
                
        # Handle Table elements - extract structured data
        elif isinstance(page,Table):
            # Get page number where table appears
            pgNum = page.metadata.page_number
            
            # Use tabula to extract table as pandas DataFrame
            # tabula provides better table extraction than unstructured
            dfs = tabula.read_pdf(fileNameWithPath,pages=pgNum)
            
            # Convert each DataFrame to Markdown format
            # Markdown preserves table structure while being text-searchable
            for df in dfs:
                # to_markdown() creates pipe-separated table:
                # | Header1 | Header2 |
                # | Value1  | Value2  |
                documentsToAdd.append(df.to_markdown(index=False))
                metadataToAdd.append({
                    "document_id" : documentId,
                    "source_heading" : currentHeading,
                    "filename" : filename,
                    "page_no" : pageNo,
                    "element_type" : type(page).__name__,  # "Table"
                    "chunk_index" : chunkIndex,
                    "upload_date" : datetime.now().strftime("%Y-%m-%d")
                })
                chunkIndex += 1
                
            # Alternative table handling (commented out):
            # Could extract both text and HTML representation
            # tableText = sanitizeText(page.text)
            # tableHtml = getattr(page.metadata,"text_as_html","")
            # fullTableContnet = f"Table Content:\n{tableText}\nHTML Structure:\n{tableHtml}"
            # documentsToAdd.append(fullTableContnet)
            # metadataToAdd.append({"source_heading": f"Table under {currentHeading}"})
    
    # Return parallel lists: documents[i] corresponds to metadataToAdd[i]
    return documentsToAdd,metadataToAdd


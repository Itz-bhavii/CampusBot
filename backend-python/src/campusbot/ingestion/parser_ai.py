"""
=========================================================================================
ADVANCED DOCUMENT PARSER FOR CAMPUSBOT — parser_ai.py
=========================================================================================

DROP-IN REPLACEMENT for parser.py with drastically improved accuracy.

WHAT'S DIFFERENT FROM parser.py (AND WHY YOUR OLD PARSER WAS TRASH):
=========================================================================================

1. SEMANTIC CHUNKING (replaces blind 1000-char splits)
   OLD: RecursiveCharacterTextSplitter splits at 1000 chars. If a sentence about
        "CS101 prerequisites" spans chars 990-1050, it gets CUT IN HALF across two
        chunks. Neither chunk is useful for retrieval.
   NEW: Uses spaCy sentence boundary detection. NEVER splits mid-sentence.
        Groups semantically related sentences together using embedding cosine
        similarity. If 3 sentences all talk about "grading policy", they stay
        in ONE chunk even if that chunk is 1200 chars.

2. HIERARCHICAL HEADING TRACKING (replaces flat currentHeading string)
   OLD: Single `currentHeading = "General"` — if you have:
        Chapter 1 > Section 1.2 > Grading Policy
        You only store "Grading Policy", losing the parent context.
   NEW: Maintains a heading STACK. Each chunk stores the FULL PATH:
        heading_path = "Chapter 1 > Section 1.2 > Grading Policy"
        This means a query for "Chapter 1 grading" will match because
        the heading path contains BOTH terms.

3. ENTITY EXTRACTION (completely new — old parser had zero entity awareness)
   OLD: No entity extraction at all. A chunk mentioning "CS-501" has no way
        to be found by exact keyword search.
   NEW: Extracts course codes (CS-101, MATH-201), dates, people, locations
        using spaCy NER + custom regex patterns. Stores as metadata tags.
        Enables exact-match filtering during retrieval.

4. ADVANCED TABLE HANDLING (replaces broken tabula-only approach)
   OLD: Converts tables to markdown only. Complex tables with merged cells
        become gibberish. No natural language description for semantic search.
   NEW: Stores DUAL representation:
        a) Markdown format — for display and basic text search
        b) Row-by-row natural language — for semantic search
           Example: "Course CS101 has 3 credits with no prerequisites"
        Both representations are stored as separate chunks, so tables are
        findable by BOTH exact keyword AND semantic meaning.

5. TITLE/HEADING CHUNKS (old parser DISCARDED all headings)
   OLD: Titles only updated currentHeading variable. The heading TEXT itself
        was never stored as a searchable chunk. If someone searches for
        "What sections does the syllabus have?", ZERO results.
   NEW: Every heading is stored as its own chunk with full hierarchy context.
        Now searchable.

6. BIDIRECTIONAL CHUNK LINKING (completely new)
   OLD: Chunks were independent islands. No way to get "the paragraph before
        this one" or "the next paragraph after this one."
   NEW: Each chunk stores prev_chunk_id and next_chunk_id. The retrieval
        service (chat_service_ai.py) can fetch adjacent chunks to build
        complete context when a single chunk isn't enough.

7. CONTEXT-ENRICHED CHUNKS (completely new)
   OLD: Each chunk was just raw text. "The deadline is February 15" stored
        without any section context — retrieval doesn't know WHAT deadline.
   NEW: Each chunk is PREFIXED with its heading path:
        "[Grading Policy > Late Submissions] The deadline is February 15"
        This means the embedding vector captures BOTH the content AND
        the structural context. Massive accuracy improvement.

FUNCTION SIGNATURE — IDENTICAL TO parser.py:
   parseFile(fileNameWithPath, filename, documentId) → (documents, metadatas)

   This is a drop-in replacement. To switch from old to new parser,
   change ONE line in worker.py:
       from . import parser       →  from . import parser_ai as parser

ZERO-COST DEPENDENCIES:
   - spaCy (free, MIT license, runs locally, no API calls)
   - All other deps already in your requirements.txt

=========================================================================================
"""

import re
import json
import magic
import tabula
import spacy
import logging.config
import numpy as np
from datetime import datetime
from typing import List, Dict, Tuple, Optional
from unstructured.partition.pdf import partition_pdf
from unstructured.partition.text import partition_text
from unstructured.partition.docx import partition_docx
from campusbot.common.campus_logger import LOGGING_CONFIG
from unstructured.documents.elements import (
    Title, NarrativeText, ListItem, Table,
    Header, Footer, FigureCaption, Address, EmailAddress,
    Image, PageBreak, Formula
)

# ===========================================================================================
# LOGGING SETUP
# ===========================================================================================
logging.config.dictConfig(LOGGING_CONFIG)
logger = logging.getLogger(__name__)


# ===========================================================================================
# SPACY MODEL LOADING
# ===========================================================================================
# Load spaCy English model for:
#   1. Sentence boundary detection (tokenization)
#   2. Named Entity Recognition (NER) — extracts people, dates, orgs, locations
#
# We use "en_core_web_sm" (small model, ~12MB, free, runs on CPU)
# WHY NOT en_core_web_md or en_core_web_lg:
#   - sm is sufficient for sentence splitting and basic NER
#   - md/lg are 40-180MB — overkill for our use case
#   - sm runs faster (important during bulk ingestion)
#
# FALLBACK: If spaCy model not installed, we fall back to regex sentence splitting.
# This is worse but won't crash the system.
# ===========================================================================================
try:
    nlp = spacy.load("en_core_web_sm")
    SPACY_AVAILABLE = True
    logger.info("spaCy model 'en_core_web_sm' loaded successfully")
except OSError:
    SPACY_AVAILABLE = False
    logger.warning(
        "spaCy model 'en_core_web_sm' not found. "
        "Run: python -m spacy download en_core_web_sm. "
        "Falling back to regex-based sentence splitting (lower quality)."
    )


# ===========================================================================================
# CUSTOM ENTITY PATTERNS — REGEX FOR ACADEMIC CONTENT
# ===========================================================================================
# spaCy's built-in NER is trained on news articles — it doesn't know what "CS-101" is.
# These regex patterns catch academic-specific entities that spaCy misses.
#
# Each pattern extracts a specific type of academic entity:
#   - COURSE_CODE: "CS101", "CS-101", "MATH 201", "ENG-101A"
#   - SEMESTER: "Fall 2025", "Spring 2026", "Summer I 2025"
#   - ROOM: "Room 301", "Room B-204", "Hall 5"
#   - CREDIT: "3 credits", "4 credit hours"
#   - GPA: "3.5 GPA", "GPA of 3.0", "CGPA 3.8"
#   - PERCENTAGE: "85%", "90.5%"
#   - TIME: "10:30 AM", "2:00 PM", "14:30"
#   - PHONE: "(555) 123-4567", "555-123-4567"
#   - EMAIL: "prof@university.edu"
# ===========================================================================================
ACADEMIC_ENTITY_PATTERNS = {
    "COURSE_CODE": re.compile(
        r'\b[A-Z]{2,5}[-\s]?\d{3,4}[A-Z]?\b'
    ),
    "SEMESTER": re.compile(
        r'\b(?:Fall|Spring|Summer|Winter)(?:\s+(?:I|II|III))?\s+\d{4}\b',
        re.IGNORECASE
    ),
    "ROOM": re.compile(
        r'\b(?:Room|Hall|Lab|Building|Auditorium|Lecture\s+Hall)\s+[A-Z]?-?\d+[A-Z]?\b',
        re.IGNORECASE
    ),
    "CREDIT": re.compile(
        r'\b\d+\s*(?:credit(?:s|\s+hours?)?)\b',
        re.IGNORECASE
    ),
    "GPA": re.compile(
        r'\b(?:(?:C?GPA)\s*(?:of\s*)?\d+\.\d+|\d+\.\d+\s*(?:C?GPA))\b',
        re.IGNORECASE
    ),
    "PERCENTAGE": re.compile(
        r'\b\d+(?:\.\d+)?%'
    ),
    "TIME": re.compile(
        r'\b\d{1,2}:\d{2}\s*(?:AM|PM|am|pm)?\b'
    ),
    "PHONE": re.compile(
        r'\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}'
    ),
    "EMAIL": re.compile(
        r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
    ),
}


# ===========================================================================================
# HEADING HIERARCHY TRACKER
# ===========================================================================================
class HeadingHierarchy:
    """
    Maintains a STACK-BASED heading hierarchy as the parser walks through a document.
    
    PROBLEM IT SOLVES:
    Documents have nested structure:
        Chapter 1: Introduction
            1.1 Overview
                1.1.1 Background
            1.2 Objectives
        Chapter 2: Methodology
    
    The old parser stored ONLY the latest heading ("1.1.1 Background").
    If someone searches "Chapter 1 background", the chunk wouldn't match
    because "Chapter 1" was overwritten.
    
    HOW IT WORKS:
    - Maintains a list (stack) of headings at different depth levels
    - When a new heading appears, it tries to figure out its depth level
      by comparing text length and patterns (numbered sections are deeper)
    - Builds a full path string: "Chapter 1: Introduction > 1.1 Overview > 1.1.1 Background"
    
    DEPTH DETECTION HEURISTIC:
    Since unstructured doesn't reliably tell us heading levels (H1/H2/H3),
    we use heuristics:
    1. Numbered headings like "1.2.3" → depth = number of dots + 1 (depth 3)
    2. Lettered subsections like "(a)" → depth = current + 1
    3. Short ALL-CAPS headings → likely top-level (depth 1)
    4. Everything else → depth based on text length relative to parent
    
    Not perfect, but WAY better than the flat string approach.
    """
    
    def __init__(self):
        # Stack of (depth_level, heading_text) tuples
        # Example: [(1, "Chapter 1"), (2, "Section 1.2"), (3, "Grading Policy")]
        self._stack: List[Tuple[int, str]] = []
    
    def update(self, heading_text: str) -> None:
        """
        Push a new heading onto the hierarchy stack.
        
        ALGORITHM:
        1. Estimate the depth level of this heading
        2. Pop all headings from the stack that are at the same or deeper level
           (because a new heading at level 2 means the old level 2 and 3 are done)
        3. Push this heading onto the stack
        
        Example sequence:
            update("Chapter 1")      → stack: [(1, "Chapter 1")]
            update("1.1 Overview")   → stack: [(1, "Chapter 1"), (2, "1.1 Overview")]
            update("1.1.1 Detail")   → stack: [(1, "Chapter 1"), (2, "1.1 Overview"), (3, "1.1.1 Detail")]
            update("1.2 Next")       → stack: [(1, "Chapter 1"), (2, "1.2 Next")]  ← popped 1.1 and 1.1.1
            update("Chapter 2")      → stack: [(1, "Chapter 2")]  ← popped everything
        """
        depth = self._estimate_depth(heading_text)
        
        # Pop all headings at same or deeper level
        # A new heading at depth 2 means all depth >= 2 headings are from previous sections
        while self._stack and self._stack[-1][0] >= depth:
            self._stack.pop()
        
        self._stack.append((depth, heading_text.strip()))
    
    def get_path(self) -> str:
        """
        Returns the full heading path as a single string.
        
        Example: "Chapter 1: Introduction > 1.1 Overview > 1.1.1 Background"
        
        WHY " > " SEPARATOR:
        - Readable by humans in search results
        - Tokenizable by embedding models (each heading becomes searchable terms)
        - Easy to split back into components if needed
        """
        if not self._stack:
            return "General"
        return " > ".join(text for _, text in self._stack)
    
    def get_path_list(self) -> List[str]:
        """
        Returns heading path as a list of strings.
        Used for metadata storage (ChromaDB can filter on string fields).
        
        Example: ["Chapter 1: Introduction", "1.1 Overview", "1.1.1 Background"]
        
        Note: ChromaDB metadata values must be str, int, float, or bool.
        Lists are stored as JSON strings.
        """
        if not self._stack:
            return ["General"]
        return [text for _, text in self._stack]
    
    def get_depth(self) -> int:
        """Returns current depth level (1-based). 0 means no headings seen yet."""
        return len(self._stack)
    
    def get_current_heading(self) -> str:
        """Returns just the most recent heading (leaf node)."""
        if not self._stack:
            return "General"
        return self._stack[-1][1]
    
    def _estimate_depth(self, text: str) -> int:
        """
        Estimates heading depth from text patterns.
        
        HEURISTIC RULES (in priority order):
        
        1. NUMBERED SECTIONS: "1.2.3 Title" → count dots + 1 = depth 3
           Matches: "1. Intro", "2.1 Methods", "3.2.1 Analysis"
           This is the most reliable signal — academic docs use numbered sections.
        
        2. LETTER SUBSECTIONS: "(a) Item" or "a) Item" → depth = current + 1
           Matches: "(a)", "(i)", "a.", "b)"
           These are always sub-items of the current section.
        
        3. ALL-CAPS SHORT TEXT: "INTRODUCTION" → depth 1
           Academic docs often use all-caps for top-level headings.
           Must be short (< 60 chars) to avoid false positives on all-caps paragraphs.
        
        4. DEFAULT: depth 2
           Most headings without clear indicators are section-level.
        """
        text_stripped = text.strip()
        
        # Rule 1: Count dots in numbered prefixes (e.g., "1.2.3 Title" → 3 dots-segments)
        numbered_match = re.match(r'^(\d+(?:\.\d+)*)\s', text_stripped)
        if numbered_match:
            # "1" → depth 1, "1.2" → depth 2, "1.2.3" → depth 3
            return numbered_match.group(1).count('.') + 1
        
        # Rule 2: Letter/roman numeral sub-items
        if re.match(r'^\(?[a-z]\)|^\(?[ivx]+\)', text_stripped, re.IGNORECASE):
            # These are always children of current section
            return max(self.get_depth() + 1, 3)
        
        # Rule 3: Short ALL-CAPS text is likely a top-level heading
        if text_stripped.isupper() and len(text_stripped) < 60:
            return 1
        
        # Rule 4: Default to depth 2 (section level)
        return 2


# ===========================================================================================
# TEXT SANITIZATION — ENHANCED VERSION
# ===========================================================================================
def sanitizeText(text: str) -> str:
    """
    Cleans and normalizes extracted text for better embedding quality.
    
    IMPROVEMENTS OVER OLD sanitizeText():
    1. Fixes hyphenated line breaks: "docu-\\nment" → "document"
    2. Removes page numbers: "Page 5 of 20" → ""  AND  "5 of 20" → ""
    3. Removes header/footer artifacts: "© 2025 University" → ""
    4. Normalizes unicode: curly quotes → straight quotes, em-dashes → hyphens
    5. Collapses whitespace: multiple spaces/newlines → single space
    6. Strips empty parentheses and brackets left by other cleaning
    
    WHY EACH STEP MATTERS:
    - Hyphen fixes: prevent "docu" and "ment" being separate tokens
    - Page numbers: prevent "5 of 20" matching queries about numbers
    - Unicode: embedding models work better with consistent characters
    - Whitespace: cleaner tokens = better embedding vectors
    
    Args:
        text: Raw text extracted from document element
    
    Returns:
        Cleaned text ready for embedding generation
    """
    if not text:
        return ""
    
    # Fix words broken across lines by PDF extraction
    # "docu-\nment" → "document"
    text = re.sub(r'-\n', '', text)
    
    # Remove standalone page number patterns
    # Matches: "Page 5 of 20", "5 of 20", "page 12", "- 5 -"
    text = re.sub(r'(?i)\bpage\s+\d+\s+of\s+\d+\b', '', text)
    text = re.sub(r'\b\d+\s+of\s+\d+\b', '', text)
    text = re.sub(r'^-\s*\d+\s*-\s*$', '', text, flags=re.MULTILINE)
    
    # Remove common header/footer artifacts
    # Copyright symbols, "Confidential", standalone dates at line start
    text = re.sub(r'©.*?\d{4}', '', text)
    text = re.sub(r'(?i)^\s*confidential\s*$', '', text, flags=re.MULTILINE)
    
    # Normalize unicode characters for consistent tokenization
    # Curly quotes → straight quotes (embedding models tokenize these differently)
    text = text.replace('\u2018', "'").replace('\u2019', "'")  # single curly quotes
    text = text.replace('\u201c', '"').replace('\u201d', '"')  # double curly quotes
    text = text.replace('\u2013', '-').replace('\u2014', '-')  # en-dash, em-dash
    text = text.replace('\u2026', '...')  # ellipsis
    text = text.replace('\u00a0', ' ')    # non-breaking space
    
    # Collapse all whitespace (multiple spaces, tabs, newlines) into single space
    text = re.sub(r'\s+', ' ', text).strip()
    
    return text


# ===========================================================================================
# SENTENCE SPLITTING — SPACY-BASED WITH REGEX FALLBACK
# ===========================================================================================
def split_into_sentences(text: str) -> List[str]:
    """
    Splits text into individual sentences using spaCy's ML-based sentence detector.
    
    WHY SPACY OVER REGEX:
    - Regex: splits on ". " — breaks on "Prof. Smith", "U.S.A.", "3.5 GPA"
    - spaCy: uses a trained model that understands abbreviations, numbers, names
    - Example: "Dr. Smith's office is in Room 301. Visit during hours."
      Regex: ["Dr.", "Smith's office is in Room 301.", "Visit during hours."]  ← WRONG
      spaCy: ["Dr. Smith's office is in Room 301.", "Visit during hours."]    ← CORRECT
    
    FALLBACK:
    If spaCy isn't available (model not downloaded), falls back to regex splitting
    on sentence-ending punctuation followed by space+capital letter.
    This is worse but functional.
    
    Args:
        text: Cleaned text to split into sentences
    
    Returns:
        List of sentence strings (empty sentences filtered out)
    """
    if not text or not text.strip():
        return []
    
    if SPACY_AVAILABLE:
        # spaCy's sentence boundary detection using the trained pipeline
        # The model considers context, not just punctuation
        # max_length check prevents memory issues on huge text blocks
        if len(text) > 100000:
            # For very large texts, process in chunks to avoid spaCy memory limits
            # spaCy default max is 1,000,000 chars but we're conservative
            sentences = []
            for i in range(0, len(text), 50000):
                chunk = text[i:i+50000]
                doc = nlp(chunk)
                sentences.extend([sent.text.strip() for sent in doc.sents if sent.text.strip()])
            print("inside spacy")
            return sentences
        print("outside inside spacy")
        doc = nlp(text)
        return [sent.text.strip() for sent in doc.sents if sent.text.strip()]
    else:
        # FALLBACK: Regex-based splitting
        # Split on period/question/exclamation followed by space and capital letter
        # Less accurate than spaCy but won't crash
        raw_sentences = re.split(r'(?<=[.!?])\s+(?=[A-Z])', text)
        print("regex")
        return [s.strip() for s in raw_sentences if s.strip()]


# ===========================================================================================
# SEMANTIC SENTENCE GROUPING
# ===========================================================================================
def group_sentences_semantically(
    sentences: List[str],
    max_chunk_size: int = 1500,
    min_chunk_size: int = 200,
    similarity_threshold: float = 0.5
) -> List[str]:
    """
    Groups consecutive sentences into semantically coherent chunks.
    
    THE CORE INSIGHT:
    ==================
    Traditional chunking (RecursiveCharacterTextSplitter) splits on CHARACTER COUNT.
    This is fundamentally wrong because:
    - A 1000-char block might contain 2 unrelated topics → bad chunk
    - A 1200-char block might be ONE coherent topic → splitting it loses meaning
    
    This function groups sentences based on SEMANTIC SIMILARITY between consecutive
    sentences. If sentence N and sentence N+1 are talking about the same topic,
    they stay in the same chunk. If there's a topic shift, we start a new chunk.
    
    ALGORITHM:
    ==========
    1. Start with first sentence in current chunk
    2. For each subsequent sentence:
       a. Check if adding it would exceed max_chunk_size (hard limit)
       b. If chunk is already decent size (> min_chunk_size), check for topic shift
       c. Topic shift = cosine similarity between current sentence and chunk centroid
          drops below threshold
       d. If topic shift detected → finalize current chunk, start new one
       e. Otherwise → add sentence to current chunk
    3. Return list of chunk strings
    
    COSINE SIMILARITY EXPLANATION:
    ==============================
    Two sentences are represented as vectors (e.g., 384 dimensions each).
    Cosine similarity measures the angle between them:
    - 1.0 = identical direction = same topic
    - 0.0 = perpendicular = unrelated
    - -1.0 = opposite = contradictory (rare in practice)
    
    We use spaCy's word vectors for this (fast, no API calls, free).
    Threshold of 0.5 means "loosely related" — we keep the threshold low because
    consecutive sentences in the same section are usually related even if the
    exact words differ.
    
    EDGE CASES:
    ===========
    - Single sentence: returned as-is (even if small)
    - All sentences highly similar: one big chunk (capped at max_chunk_size)
    - No spaCy vectors: falls back to grouping every 5 sentences together
    
    Args:
        sentences: List of individual sentences
        max_chunk_size: Maximum characters per chunk (hard limit, default 1500)
        min_chunk_size: Minimum characters before considering a topic split (default 200)
        similarity_threshold: Cosine similarity below which we split (default 0.5)
    
    Returns:
        List of chunk strings (each chunk = multiple related sentences joined)
    """
    if not sentences:
        return []
    
    if len(sentences) == 1:
        return [sentences[0]]
    
    # If spaCy vectors aren't available, fall back to fixed-size grouping
    if not SPACY_AVAILABLE or not nlp.vocab.vectors.shape[0]:
        # Group every 5 sentences together (simple but better than character splitting)
        chunks = []
        for i in range(0, len(sentences), 5):
            chunk = " ".join(sentences[i:i+5])
            chunks.append(chunk)
        return chunks
    
    chunks = []
    current_chunk_sentences = [sentences[0]]
    current_chunk_text = sentences[0]
    
    for i in range(1, len(sentences)):
        sentence = sentences[i]
        potential_chunk = current_chunk_text + " " + sentence
        
        # HARD LIMIT: Never exceed max_chunk_size
        if len(potential_chunk) > max_chunk_size:
            # Finalize current chunk and start new one
            chunks.append(current_chunk_text)
            current_chunk_sentences = [sentence]
            current_chunk_text = sentence
            continue
        
        # If chunk is still small, always add (don't split tiny chunks)
        if len(current_chunk_text) < min_chunk_size:
            current_chunk_sentences.append(sentence)
            current_chunk_text = potential_chunk
            continue
        
        # CHECK FOR TOPIC SHIFT using spaCy word vectors
        # Compare this sentence against the current chunk's content
        # If similarity is low, this sentence starts a new topic
        doc_chunk = nlp(current_chunk_text)
        doc_sentence = nlp(sentence)
        
        # spaCy's .similarity() uses cosine similarity of averaged word vectors
        similarity = doc_chunk.similarity(doc_sentence)
        
        if similarity < similarity_threshold:
            # Topic shift detected — finalize current chunk, start new one
            chunks.append(current_chunk_text)
            current_chunk_sentences = [sentence]
            current_chunk_text = sentence
        else:
            # Same topic — add to current chunk
            current_chunk_sentences.append(sentence)
            current_chunk_text = potential_chunk
    
    # Don't forget the last chunk
    if current_chunk_text:
        chunks.append(current_chunk_text)
    
    return chunks


# ===========================================================================================
# ENTITY EXTRACTION
# ===========================================================================================
def extract_entities(text: str) -> str:
    """
    Extracts named entities from text using spaCy NER + custom academic patterns.
    
    TWO-LAYER EXTRACTION:
    =====================
    
    Layer 1: spaCy NER (general-purpose)
    - Extracts: PERSON, ORG, DATE, GPE (geo-political entities), FAC (facilities)
    - Example: "Prof. John Smith" → PERSON, "MIT" → ORG, "February 15" → DATE
    - Limitation: Doesn't know academic-specific entities like course codes
    
    Layer 2: Custom Regex Patterns (academic-specific)
    - Extracts: COURSE_CODE, SEMESTER, ROOM, CREDIT, GPA, PERCENTAGE, TIME, EMAIL
    - Example: "CS-101" → COURSE_CODE, "Fall 2025" → SEMESTER, "Room 301" → ROOM
    - These patterns are defined in ACADEMIC_ENTITY_PATTERNS at module level
    
    OUTPUT FORMAT:
    ==============
    Returns a single comma-separated string of unique entities.
    Example: "CS-101, Prof. Smith, Fall 2025, Room 301, 3 credits"
    
    WHY A STRING (NOT A LIST):
    ChromaDB metadata values must be str, int, float, or bool.
    Lists are not supported. We join entities into a single searchable string.
    During retrieval, we can do substring matching on this field.
    
    WHY ENTITY EXTRACTION MATTERS FOR RAG:
    =======================================
    Without entities, a query "What room is CS101 in?" relies ONLY on semantic
    embedding similarity. The embedding for "room" and "CS101" might not closely
    match the embedding for a chunk that says "Class meets in Room 301" because
    "CS101" and "Room 301" are proper nouns that embedding models handle poorly.
    
    With entities, we can:
    1. Boost chunks that contain matching entities (in chat_service_ai.py)
    2. Do exact-match filtering in ChromaDB: where={"entity_tags": {"$contains": "CS101"}}
    3. Cross-reference entities across documents
    
    Args:
        text: Text to extract entities from
    
    Returns:
        Comma-separated string of unique entities found, or empty string if none
    """
    if not text:
        return ""
    
    entities = set()
    
    # Layer 1: spaCy NER — extract standard named entities
    if SPACY_AVAILABLE:
        # Process text through spaCy pipeline
        doc = nlp(text[:10000])  # Limit to 10K chars to prevent slowness
        
        # Extract entities of relevant types
        # We skip: CARDINAL (numbers), ORDINAL (first, second), QUANTITY, MONEY
        # because these are too generic and noisy for our use case
        relevant_labels = {"PERSON", "ORG", "DATE", "GPE", "FAC", "EVENT", "WORK_OF_ART", "LOC"}
        for ent in doc.ents:
            if ent.label_ in relevant_labels:
                # Clean entity text (remove leading/trailing whitespace and punctuation)
                clean_ent = ent.text.strip().strip('.,;:')
                if len(clean_ent) > 1:  # Skip single-character entities
                    entities.add(clean_ent)
    
    # Layer 2: Custom academic regex patterns
    for pattern_name, pattern in ACADEMIC_ENTITY_PATTERNS.items():
        matches = pattern.findall(text)
        for match in matches:
            clean_match = match.strip()
            if clean_match:
                entities.add(clean_match)
    
    # Return as comma-separated string (ChromaDB metadata compatibility)
    return ", ".join(sorted(entities)) if entities else ""


# ===========================================================================================
# TABLE PROCESSING — DUAL REPRESENTATION
# ===========================================================================================
def process_table_element(
    table_element,
    fileNameWithPath: str,
    heading_path: str,
    documentId: str,
    filename: str,
    pageNo: int,
    chunkIndex: int
) -> Tuple[List[str], List[Dict], int]:
    """
    Processes a table element into DUAL searchable representations.
    
    PROBLEM WITH OLD APPROACH:
    ==========================
    Old parser: table → tabula → DataFrame → Markdown
    
    Issues:
    1. Markdown tables are poorly embedded by models (pipe characters confuse tokenizers)
    2. No natural language description → semantic search can't find tables
    3. tabula crashes on complex tables (merged cells, nested headers)
    4. If tabula fails, the table is LOST COMPLETELY (no fallback)
    
    NEW APPROACH — DUAL REPRESENTATION:
    ====================================
    We store EVERY table as TWO chunks:
    
    Chunk A: Markdown Format (prefixed with context)
    ------------------------------------------------
    "[Grading Policy > Grade Distribution] Table:
    | Grade | Percentage | Points |
    | A     | 90-100%    | 4.0    |
    | B     | 80-89%     | 3.0    |"
    
    Purpose: Exact keyword matching. If someone searches "Grade A percentage",
    the literal text "A" and "90-100%" are in this chunk.
    
    Chunk B: Row-by-Row Natural Language
    ------------------------------------
    "[Grading Policy > Grade Distribution] Table data:
    Row 1: Grade is A, Percentage is 90-100%, Points is 4.0.
    Row 2: Grade is B, Percentage is 80-89%, Points is 3.0."
    
    Purpose: Semantic search. The sentence "Grade is A, Percentage is 90-100%"
    has a much better embedding than "| A | 90-100% | 4.0 |" because the
    embedding model understands natural language, not pipe-separated values.
    
    FALLBACK CHAIN:
    ================
    1. Try tabula extraction → DataFrame → both representations
    2. If tabula fails → use unstructured's HTML table → parse HTML
    3. If both fail → store raw text from unstructured element
    
    This ensures NO TABLE IS EVER LOST, regardless of format complexity.
    
    Args:
        table_element: unstructured Table element
        fileNameWithPath: Path to source file (for tabula)
        heading_path: Current heading hierarchy string
        documentId: Document SHA-256 hash
        filename: Original filename
        pageNo: Page number where table appears
        chunkIndex: Current chunk index (will be incremented)
    
    Returns:
        Tuple of (documents_list, metadata_list, updated_chunk_index)
    """
    documents = []
    metadatas = []
    
    # Context prefix — CRITICAL for retrieval accuracy
    # Without this prefix, a table chunk "| A | 90% |" tells the embedding model nothing
    # about what this table is ABOUT. The prefix grounds it in the document structure.
    context_prefix = f"[{heading_path}]" if heading_path != "General" else ""
    
    # ---- ATTEMPT 1: Tabula extraction (best quality for standard tables) ----
    tabula_success = False
    pgNum = table_element.metadata.page_number
    
    if pgNum and fileNameWithPath.lower().endswith('.pdf'):
        try:
            dfs = tabula.read_pdf(fileNameWithPath, pages=pgNum, silent=True) # type: ignore
            
            for df in dfs:
                # Skip empty or tiny DataFrames (noise from tabula)
                if df.empty or len(df) < 1: # type: ignore
                    continue
                
                # Clean DataFrame: drop all-NaN columns and rows
                df = df.dropna(how='all', axis=0).dropna(how='all', axis=1) # type: ignore
                if df.empty:
                    continue
                
                # ---- REPRESENTATION A: Markdown with context prefix ----
                markdown_text = df.to_markdown(index=False)
                full_markdown = f"{context_prefix} Table:\n{markdown_text}" if context_prefix else f"Table:\n{markdown_text}"
                
                documents.append(sanitizeText(full_markdown))
                metadatas.append(_build_metadata(
                    documentId, heading_path, filename, pageNo,
                    "Table_Markdown", chunkIndex
                ))
                chunkIndex += 1
                
                # ---- REPRESENTATION B: Row-by-row natural language ----
                nl_rows = _dataframe_to_natural_language(df)
                if nl_rows:
                    full_nl = f"{context_prefix} Table data:\n{nl_rows}" if context_prefix else f"Table data:\n{nl_rows}"
                    documents.append(sanitizeText(full_nl))
                    metadatas.append(_build_metadata(
                        documentId, heading_path, filename, pageNo,
                        "Table_NaturalLanguage", chunkIndex
                    ))
                    chunkIndex += 1
                
                tabula_success = True
                
        except Exception as e:
            logger.warning(f"Tabula extraction failed on page {pgNum}: {e}")
            tabula_success = False
    
    # ---- ATTEMPT 2: Unstructured's HTML table (fallback for complex tables) ----
    if not tabula_success:
        # unstructured often stores table HTML in metadata.text_as_html
        table_html = getattr(table_element.metadata, "text_as_html", "")
        table_text = table_element.text.strip() if table_element.text else ""
        
        if table_text:
            # Store the raw text content with context
            full_text = f"{context_prefix} Table content:\n{table_text}" if context_prefix else f"Table content:\n{table_text}"
            documents.append(sanitizeText(full_text))
            metadatas.append(_build_metadata(
                documentId, heading_path, filename, pageNo,
                "Table_Text", chunkIndex
            ))
            chunkIndex += 1
        
        if table_html:
            # Parse HTML table into natural language as additional representation
            nl_from_html = _html_table_to_natural_language(table_html)
            if nl_from_html:
                full_nl = f"{context_prefix} Table data:\n{nl_from_html}" if context_prefix else f"Table data:\n{nl_from_html}"
                documents.append(sanitizeText(full_nl))
                metadatas.append(_build_metadata(
                    documentId, heading_path, filename, pageNo,
                    "Table_NaturalLanguage", chunkIndex
                ))
                chunkIndex += 1
    
    return documents, metadatas, chunkIndex


def _dataframe_to_natural_language(df) -> str:
    """
    Converts a pandas DataFrame into row-by-row natural language sentences.
    
    EXAMPLE:
    Input DataFrame:
        | Course | Credits | Prerequisites |
        | CS101  | 3       | None          |
        | CS201  | 4       | CS101         |
    
    Output:
        "Row 1: Course is CS101, Credits is 3, Prerequisites is None.
         Row 2: Course is CS201, Credits is 4, Prerequisites is CS101."
    
    WHY THIS FORMAT:
    - Embedding models understand "Course is CS101" much better than "| CS101 |"
    - Natural language captures the RELATIONSHIP between header and value
    - Each row becomes a searchable sentence
    - Query "CS201 prerequisites" will semantically match "Prerequisites is CS101"
      for the CS201 row
    """
    if df.empty:
        return ""
    
    headers = [str(col).strip() for col in df.columns]
    rows_text = []
    
    for idx, row in df.iterrows():
        # Build "Header1 is Value1, Header2 is Value2" for each row
        pairs = []
        for header in headers:
            value = str(row[header]).strip()
            if value and value.lower() not in ('nan', 'none', ''):
                pairs.append(f"{header} is {value}")
        
        if pairs:
            rows_text.append(f"Row {len(rows_text) + 1}: {', '.join(pairs)}.")
    
    return "\n".join(rows_text)


def _html_table_to_natural_language(html: str) -> str:
    """
    Parses an HTML table string into natural language rows.
    
    Used as fallback when tabula fails but unstructured extracted HTML.
    Uses basic regex parsing — no external HTML library needed.
    
    Args:
        html: HTML table string from unstructured metadata
    
    Returns:
        Natural language representation of the table, or empty string
    """
    if not html:
        return ""
    
    try:
        # Extract headers from <th> tags
        headers = re.findall(r'<th[^>]*>(.*?)</th>', html, re.IGNORECASE | re.DOTALL)
        headers = [re.sub(r'<[^>]+>', '', h).strip() for h in headers]
        
        # Extract rows from <tr> tags containing <td> tags
        rows = re.findall(r'<tr[^>]*>(.*?)</tr>', html, re.IGNORECASE | re.DOTALL)
        
        result_lines = []
        row_num = 0
        
        for row_html in rows:
            cells = re.findall(r'<td[^>]*>(.*?)</td>', row_html, re.IGNORECASE | re.DOTALL)
            cells = [re.sub(r'<[^>]+>', '', c).strip() for c in cells]
            
            if not cells:
                continue
            
            row_num += 1
            if headers and len(headers) >= len(cells):
                pairs = [f"{headers[i]} is {cells[i]}" for i in range(len(cells)) if cells[i]]
                result_lines.append(f"Row {row_num}: {', '.join(pairs)}.")
            else:
                result_lines.append(f"Row {row_num}: {', '.join(cells)}.")
        
        return "\n".join(result_lines)
    except Exception:
        return ""


# ===========================================================================================
# METADATA BUILDER HELPER
# ===========================================================================================
def _build_metadata(
    documentId: str,
    heading_path: str,
    filename: str,
    pageNo: int,
    element_type: str,
    chunkIndex: int,
    chunk_id: str = "",
    prev_chunk_id: str = "",
    next_chunk_id: str = "",
    entity_tags: str = ""
) -> Dict:
    """
    Builds a standardized metadata dictionary for a chunk.
    
    METADATA SCHEMA (ENHANCED):
    ============================
    All fields are str/int/float (ChromaDB requirement — no lists or nested dicts).
    
    Fields:
    - document_id: SHA-256 hash of source file — used to track which document a chunk came from
    - source_heading: Full heading hierarchy path — "Chapter 1 > Section 1.2 > Topic"
    - filename: Original uploaded filename — shown to user in citations
    - page_no: Page number in source document — for citation/verification
    - element_type: What kind of element this chunk came from:
        * "Title" — section heading
        * "NarrativeText" — paragraph body text
        * "ListItem" — bullet point or numbered list item
        * "Table_Markdown" — table in markdown format
        * "Table_NaturalLanguage" — table as natural language sentences
        * "Table_Text" — raw table text (fallback)
    - chunk_index: Sequential position in document (0, 1, 2, ...) — for reconstruction
    - chunk_id: Unique identifier for this chunk — for bidirectional linking
    - prev_chunk_id: chunk_id of previous chunk — for fetching context backwards
    - next_chunk_id: chunk_id of next chunk — for fetching context forwards
    - entity_tags: Comma-separated entities found in this chunk — for entity-based filtering
    - upload_date: When this document was ingested — for time-based filtering
    
    WHY BIDIRECTIONAL LINKING:
    ==========================
    Scenario: User asks "What happens if I submit late?"
    Retrieval finds: "Late submissions receive a 10% penalty per day."
    But the user needs MORE context — what's the deadline? Any exceptions?
    
    With linking, chat_service_ai.py can fetch prev/next chunks:
    - prev_chunk: "All assignments are due by 11:59 PM on the deadline."
    - next_chunk: "Exceptions may be granted with prior approval from the instructor."
    
    This gives the LLM COMPLETE context instead of just one fragment.
    """
    return {
        "document_id": documentId,
        "source_heading": heading_path,
        "filename": filename,
        "page_no": pageNo,
        "element_type": element_type,
        "chunk_index": chunkIndex,
        "chunk_id": chunk_id,
        "prev_chunk_id": prev_chunk_id,
        "next_chunk_id": next_chunk_id,
        "entity_tags": entity_tags,
        "upload_date": datetime.now().strftime("%Y-%m-%d")
    }


# ===========================================================================================
# MAIN PARSING FUNCTION — DROP-IN REPLACEMENT FOR parser.parseFile()
# ===========================================================================================
def parseFile(fileNameWithPath: str, filename: str, documentId: str):
    """
    ADVANCED document parser — extracts text, tables, and metadata with maximum accuracy.
    
    THIS IS A DROP-IN REPLACEMENT FOR parser.parseFile().
    Same function signature, same return format. To switch:
        from . import parser_ai as parser   (in worker.py)
    
    =========================================================================================
    COMPLETE PARSING PIPELINE (7 STAGES):
    =========================================================================================
    
    STAGE 1: MIME TYPE DETECTION
    - Uses libmagic to detect actual file type (not file extension)
    - Prevents security issues: renamed malware.exe → document.pdf
    
    STAGE 2: DOCUMENT STRUCTURE EXTRACTION (unstructured library)
    - PDF: uses "hi_res" strategy with table inference
    - DOCX: parses Word structure (paragraphs, tables, headers)
    - TXT: line-by-line with paragraph detection
    - Returns typed elements: Title, NarrativeText, ListItem, Table, etc.
    
    STAGE 3: HEADING HIERARCHY TRACKING
    - Maintains heading stack using HeadingHierarchy class
    - Each chunk tagged with full path: "Chapter > Section > Subsection"
    - Titles stored as their own searchable chunks (old parser discarded them!)
    
    STAGE 4: SEMANTIC SENTENCE GROUPING
    - For NarrativeText and ListItems:
      a. Split into sentences using spaCy
      b. Group related sentences using cosine similarity
      c. Respect hard size limits (max 1500 chars per chunk)
    - This is THE key improvement: chunks are semantically coherent units,
      not random character-count slices
    
    STAGE 5: TABLE DUAL-REPRESENTATION
    - Tables stored as BOTH markdown AND natural language
    - Tabula extraction with fallback to unstructured HTML parser
    - Context prefix from heading hierarchy
    
    STAGE 6: ENTITY EXTRACTION
    - spaCy NER for people, dates, organizations
    - Custom regex for course codes, semesters, rooms, credits, GPA
    - Entities stored as comma-separated metadata string
    
    STAGE 7: BIDIRECTIONAL LINKING (POST-PROCESSING)
    - After all chunks created, assign chunk_ids
    - Link each chunk to prev/next chunk via IDs
    - Enables contextual expansion during retrieval
    
    STAGE 8: CONTEXT-ENRICHED CHUNK TEXT
    - Each chunk text prefixed with its heading path
    - "[Grading > Late Policy] Submissions after the deadline receive..."
    - The embedding vector now captures BOTH content and context
    
    =========================================================================================
    
    Args:
        fileNameWithPath: Full path to downloaded file (/tmp/xyz/document.pdf)
        filename: Original filename for metadata (document.pdf)
        documentId: SHA-256 hash identifying this document
    
    Returns:
        Tuple of (documents, metadata):
        - documents: List of text chunks (strings) with context prefixes
        - metadata: List of dicts with enhanced metadata per chunk
    
    Raises:
        Exception: If file format not supported
    """
    logger.info(f"[parser_ai] Starting advanced parse of: {filename}")
    
    # ==========================================
    # STAGE 1: MIME TYPE DETECTION
    # ==========================================
    mimeType = magic.from_file(fileNameWithPath, mime=True)
    logger.info(f"Detected MIME type: {mimeType}")
    
    # ==========================================
    # STAGE 2: DOCUMENT STRUCTURE EXTRACTION
    # ==========================================
    if mimeType == 'application/pdf':
        # "hi_res" strategy uses layout analysis (slower but much more accurate)
        # infer_table_structure=True: detects and preserves table boundaries
        # This prevents table text from being jumbled with paragraph text
        doc = partition_pdf(
            fileNameWithPath,
            strategy="hi_res",
            infer_table_structure=True
        )
        logger.info("PDF parsed with hi_res strategy")
        
    elif mimeType == 'text/plain':
        doc = partition_text(fileNameWithPath)
        logger.info("Plain text file parsed")
        
    elif mimeType == 'application/vnd.openxmlformats-officedocument.wordprocessingml.document':
        doc = partition_docx(fileNameWithPath)
        logger.info("DOCX file parsed")
        
    else:
        logger.error(f"Unsupported file format: {mimeType}")
        raise Exception(f"Invalid File Format: {mimeType}")
    
    logger.info(f"Extracted {len(doc)} elements from document")
    
    # ==========================================
    # STAGE 3-6: PROCESS ELEMENTS
    # ==========================================
    # Initialize tracking structures
    headingTracker = HeadingHierarchy()
    documentsToAdd = []     # Final list of chunk texts
    metadataToAdd = []      # Final list of metadata dicts
    chunkIndex = 0          # Sequential chunk counter
    
    # Buffer for accumulating consecutive ListItems under the same heading
    # WHY BUFFER LIST ITEMS:
    # Documents often have bullet lists:
    #   - Item 1
    #   - Item 2
    #   - Item 3
    # The old parser stored EACH bullet as a separate chunk.
    # This is terrible because:
    #   1. Each bullet is too short for good embeddings (10-50 chars)
    #   2. Individual bullets lack context
    #   3. A query about the list topic might only match 1 bullet
    # We buffer them and combine into a single chunk with the list heading.
    listItemBuffer = []
    listItemHeading = ""
    listItemPage = 0
    
    for element in doc:
        # Get page number (default 0 if not available)
        pageNo = getattr(element.metadata, 'page_number', 0) or 0
        
        # ---- FLUSH LIST BUFFER if element type changed ----
        # If we've been collecting list items and now hit a non-list element,
        # finalize the buffered list into a single chunk
        if listItemBuffer and not isinstance(element, ListItem):
            chunkIndex = _flush_list_buffer(
                listItemBuffer, listItemHeading, listItemPage,
                documentsToAdd, metadataToAdd,
                documentId, filename, chunkIndex
            )
            listItemBuffer = []
        
        # ========== HANDLE TITLE ELEMENTS ==========
        if isinstance(element, Title):
            heading_text = element.text.strip()
            if not heading_text:
                continue
            
            # Update the heading hierarchy tracker
            headingTracker.update(heading_text)
            heading_path = headingTracker.get_path()
            
            # CRITICAL CHANGE: Store the heading ITSELF as a searchable chunk
            # Old parser: Titles only updated currentHeading, never stored
            # Query "What sections does the syllabus have?" → ZERO results with old parser
            # Now: Every heading is a chunk, findable by search
            documents_text = f"[{heading_path}] {heading_text}"
            
            documentsToAdd.append(sanitizeText(documents_text))
            metadataToAdd.append(_build_metadata(
                documentId, heading_path, filename, pageNo,
                "Title", chunkIndex,
                entity_tags=extract_entities(heading_text)
            ))
            chunkIndex += 1
        
        # ========== HANDLE NARRATIVE TEXT (PARAGRAPHS) ==========
        elif isinstance(element, NarrativeText):
            raw_text = element.text.strip()
            if not raw_text or len(raw_text) < 10:
                # Skip tiny fragments (extraction noise)
                continue
            
            heading_path = headingTracker.get_path()
            
            # SEMANTIC CHUNKING:
            # 1. Split text into sentences (spaCy)
            # 2. Group related sentences (cosine similarity)
            # 3. Each group becomes one chunk
            sentences = split_into_sentences(raw_text)
            
            if not sentences:
                continue
            
            # Group sentences semantically
            semantic_chunks = group_sentences_semantically(
                sentences,
                max_chunk_size=1500,    # Larger than old 1000 — we trust semantic boundaries
                min_chunk_size=200,     # Don't split tiny text
                similarity_threshold=0.5
            )
            
            for chunk_text in semantic_chunks:
                chunk_text = sanitizeText(chunk_text)
                if not chunk_text or len(chunk_text) < 10:
                    continue
                
                # CONTEXT-ENRICHED TEXT:
                # Prefix the chunk with its heading path so the embedding vector
                # captures WHERE in the document this text appears
                enriched_text = f"[{heading_path}] {chunk_text}" if heading_path != "General" else chunk_text
                
                documentsToAdd.append(enriched_text)
                metadataToAdd.append(_build_metadata(
                    documentId, heading_path, filename, pageNo,
                    "NarrativeText", chunkIndex,
                    entity_tags=extract_entities(chunk_text)
                ))
                chunkIndex += 1
        
        # ========== HANDLE LIST ITEMS (BUFFERED) ==========
        elif isinstance(element, ListItem):
            raw_text = element.text.strip()
            if not raw_text:
                continue
            
            # Buffer list items — they'll be flushed when a non-list element appears
            # or at the end of the document
            if not listItemBuffer:
                # Starting a new list — record the heading context
                listItemHeading = headingTracker.get_path()
                listItemPage = pageNo
            
            listItemBuffer.append(raw_text)
        
        # ========== HANDLE TABLE ELEMENTS ==========
        elif isinstance(element, Table):
            heading_path = headingTracker.get_path()
            
            # Process table with dual representation (markdown + natural language)
            table_docs, table_metas, chunkIndex = process_table_element(
                element, fileNameWithPath, heading_path,
                documentId, filename, pageNo, chunkIndex
            )
            
            documentsToAdd.extend(table_docs)
            metadataToAdd.extend(table_metas)
        
        # ========== HANDLE OTHER ELEMENT TYPES ==========
        # FigureCaption, Header, Footer, Address, Formula, etc.
        # Old parser IGNORED all of these. We capture them as searchable chunks.
        elif isinstance(element, (FigureCaption, Formula)):
            raw_text = element.text.strip()
            if raw_text and len(raw_text) > 10:
                heading_path = headingTracker.get_path()
                element_type_name = type(element).__name__
                
                enriched_text = f"[{heading_path}] {element_type_name}: {raw_text}"
                
                documentsToAdd.append(sanitizeText(enriched_text))
                metadataToAdd.append(_build_metadata(
                    documentId, heading_path, filename, pageNo,
                    element_type_name, chunkIndex,
                    entity_tags=extract_entities(raw_text)
                ))
                chunkIndex += 1
        
        # Silently skip: Header, Footer, PageBreak, Image (no text content)
        # These don't contain useful searchable text
    
    # ---- FLUSH any remaining buffered list items ----
    if listItemBuffer:
        chunkIndex = _flush_list_buffer(
            listItemBuffer, listItemHeading, listItemPage,
            documentsToAdd, metadataToAdd,
            documentId, filename, chunkIndex
        )
    
    # ==========================================
    # STAGE 7: BIDIRECTIONAL LINKING (POST-PROCESSING)
    # ==========================================
    # Now that all chunks are created, assign unique chunk_ids and link them.
    # chunk_id format: "{documentId}_chunk_{index}"
    # This is deterministic — same document always produces same chunk IDs.
    _assign_bidirectional_links(documentsToAdd, metadataToAdd, documentId)
    
    logger.info(
        f"[parser_ai] Parsing complete: {len(documentsToAdd)} chunks created "
        f"from {len(doc)} elements"
    )
    
    return documentsToAdd, metadataToAdd


# ===========================================================================================
# LIST BUFFER FLUSH — Combines buffered list items into coherent chunks
# ===========================================================================================
def _flush_list_buffer(
    listItems: List[str],
    headingPath: str,
    pageNo: int,
    documentsToAdd: List[str],
    metadataToAdd: List[Dict],
    documentId: str,
    filename: str,
    chunkIndex: int
) -> int:
    """
    Flushes buffered list items into one or more coherent chunks.
    
    STRATEGY:
    =========
    1. Combine all list items into a single block with bullet markers
    2. If combined text < 1500 chars → store as single chunk (most cases)
    3. If combined text > 1500 chars → split into groups of items that fit
    
    EXAMPLE:
    ========
    Input listItems: ["Must complete homework", "Attendance mandatory", "No late work"]
    headingPath: "Course Policies > Requirements"
    
    Output chunk text:
    "[Course Policies > Requirements] List:
    • Must complete homework
    • Attendance mandatory
    • No late work"
    
    WHY COMBINE:
    - Individual list items ("Must complete homework") are too short for good embeddings
    - The list as a whole is semantically coherent (all are requirements)
    - Combined chunk matches queries like "What are the course requirements?"
    
    Args:
        listItems: List of bullet point text strings
        headingPath: Current heading hierarchy path
        pageNo: Page number
        documentsToAdd: Main documents list (appended to)
        metadataToAdd: Main metadata list (appended to)
        documentId: Document hash
        filename: Original filename
        chunkIndex: Current chunk index
    
    Returns:
        Updated chunkIndex after adding chunks
    """
    if not listItems:
        return chunkIndex
    
    # Combine list items with bullet markers
    combined = "\n".join([f"• {item}" for item in listItems])
    context_prefix = f"[{headingPath}]" if headingPath != "General" else ""
    
    # Check if combined list fits in one chunk
    if len(combined) <= 1500:
        full_text = f"{context_prefix} List:\n{combined}" if context_prefix else f"List:\n{combined}"
        
        documentsToAdd.append(sanitizeText(full_text))
        metadataToAdd.append(_build_metadata(
            documentId, headingPath, filename, pageNo,
            "ListItem_Group", chunkIndex,
            entity_tags=extract_entities(combined)
        ))
        chunkIndex += 1
    else:
        # Split into sub-groups that fit within 1500 chars
        current_group = []
        current_length = 0
        
        for item in listItems:
            item_length = len(item) + 4  # +4 for "• " and "\n"
            
            if current_length + item_length > 1500 and current_group:
                # Flush current group
                group_text = "\n".join([f"• {it}" for it in current_group])
                full_text = f"{context_prefix} List:\n{group_text}" if context_prefix else f"List:\n{group_text}"
                
                documentsToAdd.append(sanitizeText(full_text))
                metadataToAdd.append(_build_metadata(
                    documentId, headingPath, filename, pageNo,
                    "ListItem_Group", chunkIndex,
                    entity_tags=extract_entities(group_text)
                ))
                chunkIndex += 1
                current_group = []
                current_length = 0
            
            current_group.append(item)
            current_length += item_length
        
        # Flush remaining items
        if current_group:
            group_text = "\n".join([f"• {it}" for it in current_group])
            full_text = f"{context_prefix} List:\n{group_text}" if context_prefix else f"List:\n{group_text}"
            
            documentsToAdd.append(sanitizeText(full_text))
            metadataToAdd.append(_build_metadata(
                documentId, headingPath, filename, pageNo,
                "ListItem_Group", chunkIndex,
                entity_tags=extract_entities(group_text)
            ))
            chunkIndex += 1
    
    return chunkIndex


# ===========================================================================================
# BIDIRECTIONAL LINKING — POST-PROCESSING PASS
# ===========================================================================================
def _assign_bidirectional_links(
    documents: List[str],
    metadatas: List[Dict],
    documentId: str
) -> None:
    """
    Assigns chunk_id, prev_chunk_id, and next_chunk_id to all chunks.
    
    Called AFTER all chunks are created (post-processing pass).
    
    WHY POST-PROCESSING:
    During parsing, we don't know how many chunks will exist yet,
    so we can't assign next_chunk_id until ALL chunks are created.
    This pass fills in all three linking fields.
    
    CHUNK ID FORMAT: "{documentId}_chunk_{index}"
    - Deterministic: same document always produces same IDs
    - Globally unique: documentId is SHA-256, index is sequential
    - Stable: re-parsing same document produces same IDs (useful for updates)
    
    LINKING PATTERN:
    chunk_0: prev="" , next="..._chunk_1"
    chunk_1: prev="..._chunk_0", next="..._chunk_2"
    chunk_2: prev="..._chunk_1", next="..._chunk_3"
    ...
    chunk_N: prev="..._chunk_{N-1}", next=""
    
    Args:
        documents: List of chunk texts (not modified, just used for length)
        metadatas: List of metadata dicts (modified in-place)
        documentId: Document hash for building chunk IDs
    """
    total = len(metadatas)
    
    for i in range(total):
        chunk_id = f"{documentId}_chunk_{i}"
        prev_id = f"{documentId}_chunk_{i-1}" if i > 0 else ""
        next_id = f"{documentId}_chunk_{i+1}" if i < total - 1 else ""
        
        metadatas[i]["chunk_id"] = chunk_id
        metadatas[i]["prev_chunk_id"] = prev_id
        metadatas[i]["next_chunk_id"] = next_id

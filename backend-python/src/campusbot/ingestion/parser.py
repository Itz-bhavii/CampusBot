import re
import magic
import tabula
import logging.config
from unstructured.partition.pdf import partition_pdf
from unstructured.partition.text import partition_text
from unstructured.partition.docx import partition_docx
from campusbot.common.campus_logger import LOGGING_CONFIG
from langchain_text_splitters import RecursiveCharacterTextSplitter
from unstructured.documents.elements import Title,NarrativeText,ListItem,Table

logging.config.dictConfig(LOGGING_CONFIG)
logger = logging.getLogger(__name__)



def sanitizeText(text: str) -> str:
    #  Fix words broken across lines
    text = re.sub(r'-\n', '', text)
    #  Remove page numbers, headers, footers
    text = re.sub(r'\d+ of \d+', '', text)
    #  eollapse all whitespace into single spaces
    text = re.sub(r'\s+', ' ', text).strip()
    return text

def parseFile(fileNameWithPath:str):
    print("successfully entered parsed")
    mimeType = magic.from_file(fileNameWithPath,mime=True)
    if(mimeType == 'application/pdf'):
        doc = partition_pdf(fileNameWithPath,strategy="hi_res",infer_table_structure=True)
        logger.info("Opened The Pdf File")
    elif(mimeType == 'text/plain'):
        doc = partition_text(fileNameWithPath)
        logger.info("Opened The Text File")
    elif(mimeType == 'application/vnd.openxmlformats-officedocument.wordprocessingml.document'):
        doc = partition_docx(fileNameWithPath)
    else:
        logger.error("Invalid File Format")
        raise Exception("Invalid File Format")
    
    textSplitter = RecursiveCharacterTextSplitter(
        chunk_size = 1000,
        chunk_overlap = 200,
        separators=["\n\n","\n"," ",""]
    )

    documentsToAdd = []
    metadataToAdd = []
    currentHeading = "General"
    for page in doc:

        if isinstance(page,Title):
            currentHeading = page.text.strip()

        elif isinstance(page,NarrativeText) or isinstance(page,ListItem):
            if len(page.text) < 1000 :
                documentsToAdd.append(sanitizeText(page.text.strip()))
                metadataToAdd.append({"source_heading" : currentHeading})
            else :
                subChunks = textSplitter.split_text(page.text)
                for chunk in subChunks:
                    documentsToAdd.append(sanitizeText(chunk))
                    metadataToAdd.append({"source_heading" : currentHeading})
        elif isinstance(page,Table):
            pgNum = page.metadata.page_number
            dfs = tabula.read_pdf(fileNameWithPath,pages=pgNum)
            for df in dfs:
                documentsToAdd.append(df.to_markdown(index=False))
                metadataToAdd.append({"source_heading": f"Table under {currentHeading}"})
            # tableText = sanitizeText(page.text)
            # tableHtml = getattr(page.metadata,"text_as_html","")
            # fullTableContnet = f"Table Content:\n{tableText}\nHTML Structure:\n{tableHtml}"
            # documentsToAdd.append(fullTableContnet)
            # metadataToAdd.append({"source_heading": f"Table under {currentHeading}"})
            
    return documentsToAdd,metadataToAdd


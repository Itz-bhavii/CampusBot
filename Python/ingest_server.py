import os
import uuid
import chromadb
import pymupdf
import pytesseract
import logging
import logging.config
from PIL import Image
from flask import Flask,request,jsonify;
from google import genai
from dotenv import load_dotenv
from chromadb.utils import embedding_functions
from unstructured.partition.pdf import partition_pdf
from unstructured.partition.text import partition_text
from logging_config import LOGGING_CONFIG

# POPPLER_PATH_BIN = r"D:\Temp\Python Libraries\poppler-25.07.0\Library\bin"


logging.config.dictConfig(LOGGING_CONFIG)

logger = logging.getLogger(__name__)

load_dotenv()
API_KEY = os.getenv("API_KEY")

if not API_KEY:
    logger.critical("API_KEY value not set")
    raise ValueError("API_KEY not set")

try:
    model = embedding_functions.SentenceTransformerEmbeddingFunction(
        model_name="all-MiniLM-L6-v2"
    )
    app = Flask(__name__)
    chromaClient = chromadb.HttpClient(host="localhost",port=8000)
    googleClient = genai.Client(api_key=API_KEY)
    collection = chromaClient.get_or_create_collection(name="practice_collection",embedding_function=model)
    logger.info("Successfully initialized all clients and connected to ChromaDB.")

except Exception as e:
    logger.critical("Failed during application initialization.", exc_info=True)
    exit(1)

# chromaClient.delete_collection("practice_collection")

pytesseract.pytesseract.tesseract_cmd = r'C:/Program Files/Tesseract-OCR/tesseract.exe'

@app.route("/ingest-image",methods = ['POST'])
def getImage():
    content = request.get_json()
    imagePath = content["path"]
    if not imagePath:
        logger.error("image path not received")
        return jsonify({"error": "Missing 'path' in request body"}), 400

    logger.info("Path Extracted Successfully")
    image = Image.open(imagePath)
    imageDataText = pytesseract.image_to_string(image)
    logger.info("Image Data Extracted Successfully")
    extractAndStoreText(imageDataText) 
    textToReturn = {
        "content" : "Data Extracted Successfully"
    }
    return jsonify(textToReturn)



@app.route('/ingest',methods = ['POST'])
def addText():
    content = request.get_json()
    fileNameWithPath = content["path"]
    if not fileNameWithPath:
        logger.error("image path not received")
        return jsonify({"error": "Missing 'path' in request body"}), 400
    logger.info("Extracted Path")
    textToReturn = getFileDataAndExtract(fileNameWithPath)

    return jsonify(textToReturn)



@app.route("/embed",methods = ['GET'])
def getAll():
    list = collection.get(include=["documents"])
    list = list["documents"]
    logger.info("Extracted Text")
    return jsonify(list)

@app.route("/querry",methods=['POST'])
def getQuerry():
    content = request.get_json()
    question = content["question"]
    if not question:
        return jsonify({"error": "Missing 'question' in request body"}), 400
    logger.info("Received /querry request.", extra={'question': question})
    result = collection.query(
        query_texts=[question],
        n_results= 3
    )
    logger.info("Extracted The Matching Results")

    prompt = f"Using only the provided context, answer the question. Context: [{result["documents"]}]. Question: [{question}]"

    logger.info("Calling Model")
    response = googleClient.models.generate_content(
        model="gemini-2.0-flash",
        contents=[prompt]
    )
    logger.info("Response Generated")

    ans = {
        "answer":response.text
    }
    return jsonify(ans)


@app.route("/health")
def healthChecker():
    textToReturn = {
        "status":"healthy"
    }
    return textToReturn


def cleanText(text):
    cleanedText = ' '.join(str(text).split())
    return cleanedText

def extractAndStoreText(fullText):
    primaryChunks = fullText.split("\n\n")
    finalText = []
    logger.info("Chunking The Received Text")
    for chunk in primaryChunks:
        if(len(chunk) > 1000):
            smallChunk = chunk.split("\n")
            for small in smallChunk:
                finalText.append(cleanText(small))
        else:
            finalText.append(cleanText(chunk))
        
    if finalText:
        logger.info("Assigning Uids")
        uuids = [str(uuid.uuid4()) for _ in finalText]
        collection.add(
            ids= uuids,
            documents= finalText
        )
        logger.info("Text Added To The Database Successfully")

    return finalText


def getFileDataAndExtract(fileName:str):
    if(".pdf" in fileName):
        doc = partition_pdf(fileName,strategy="hi_res")
        logger.info("Opened The Pdf File")
    elif(".txt" in fileName):
        doc = partition_text(fileName)
        logger.info("Opened The Text File")
    else:
        logger.error("Invalid File Format")
        raise Exception("Invalid File Format")
    fullText = ""
    for page in doc:
        fullText += page.text + "\n"

    extractAndStoreText(fullText)

    textToReturn = {
        "content" : "Text Extracted Successfully"
    }

    return textToReturn

if(__name__== "__main__"):
    app.run(debug=True)

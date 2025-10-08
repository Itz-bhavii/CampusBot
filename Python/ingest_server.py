import os
import uuid
import chromadb
import pymupdf
import pytesseract
from PIL import Image
from flask import Flask,request,jsonify;
from google import genai
from dotenv import load_dotenv
from chromadb.utils import embedding_functions

load_dotenv()
API_KEY = os.getenv("API_KEY")

model = embedding_functions.SentenceTransformerEmbeddingFunction(
    model_name="all-MiniLM-L6-v2"
)

app = Flask(__name__)
chromaClient = chromadb.HttpClient(host="localhost",port=8000)
googleClient = genai.Client(api_key=API_KEY)
pytesseract.pytesseract.tesseract_cmd = r'C:/Program Files/Tesseract-OCR/tesseract.exe'

chromaClient.delete_collection("practice_collection")
collection = chromaClient.get_or_create_collection(name="practice_collection",embedding_function=model)



@app.route("/ingest-image",methods = ['POST'])
def getImage():
    content = request.get_json()
    imagePath = content["path"]
    image = Image.open(imagePath)
    imageDataText = pytesseract.image_to_string(image)
    finalText = extractAndStoreText(imageDataText) 
    textToReturn = {
        "content" : str(finalText)
    }
    return jsonify(textToReturn)



@app.route('/ingest',methods = ['POST'])
def addText():
    content = request.get_json()
    fileName = content["path"]
    doc = pymupdf.open(fileName)
    fullText = ""
    for page in doc:
        fullText += page.get_text() + "\n"

    # primaryChunks = fullText.split("\n\n")
    # finalText = []
    # for chunk in primaryChunks:
    #     if(len(chunk) > 1000):
    #         smallChunk = chunk.split("\n")
    #         for small in smallChunk:
    #             finalText.append(small)
    #     else:
    #         finalText.append(chunk)
        
    # if finalText:
    #     uuids = [str(uuid.uuid4()) for _ in finalText]
    #     collection.add(
    #         ids= uuids,
    #         documents= finalText
    #     )
    finalText = extractAndStoreText(fullText)

    textToReturn = {
        "content" : str(finalText)
    }


    return jsonify(textToReturn)

@app.route("/embed",methods = ['GET'])
def getAll():
    list = collection.get(include=["documents"])
    list = list["documents"]
    return jsonify(list)

@app.route("/querry",methods=['POST'])
def getQuerry():
    content = request.get_json()
    question = content["question"]
    result = collection.query(
        query_texts=[question],
        n_results= 3
    )

    prompt = f"Using only the provided context, answer the question. Context: [{result["documents"]}]. Question: [{question}]"

    response = googleClient.models.generate_content(
        model="gemini-2.0-flash",
        contents=[prompt]
    )

    ans = {
        "answer":response.text
    }
    return jsonify(ans)


def cleanText(text):
    cleanedText = ' '.join(str(text).split())
    return cleanedText

def extractAndStoreText(fullText):
    primaryChunks = fullText.split("\n\n")
    finalText = []
    for chunk in primaryChunks:
        if(len(chunk) > 1000):
            smallChunk = chunk.split("\n")
            for small in smallChunk:
                finalText.append(cleanText(small))
        else:
            finalText.append(cleanText(chunk))
        
    if finalText:
        uuids = [str(uuid.uuid4()) for _ in finalText]
        collection.add(
            ids= uuids,
            documents= finalText
        )

    return finalText

app.run(debug=True)
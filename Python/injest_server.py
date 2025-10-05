from flask import Flask,request,jsonify;
from google import genai
from dotenv import load_dotenv
import os
import uuid
import chromadb
import pymupdf

load_dotenv()
API_KEY = os.getenv("API_KEY")


app = Flask(__name__)
chromaClient = chromadb.HttpClient(host="localhost",port=8000)
googleClient = genai.Client(api_key=API_KEY)

collection = chromaClient.get_or_create_collection("practice_collection")

# chromaClient.delete_collection("practice_collection")

@app.route('/embed',methods = ['POST'])
def addText():
    content = request.get_json()
    fileName = content["filePath"]
    doc = pymupdf.open(fileName)
    fullText = ""
    for page in doc:
        fullText += page.get_text() + "\n"

    primaryChunks = fullText.split("\n\n")
    finalText = []
    for chunk in primaryChunks:
        if(len(chunk) > 1000):
            smallChunk = chunk.split("\n")
            for small in smallChunk:
                finalText.append(small)
        else:
            finalText.append(chunk)
        
    if finalText:
        uuids = [str(uuid.uuid4()) for _ in finalText]
        collection.add(
            ids= uuids,
            documents= finalText
        )
    
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


app.run(debug=True)
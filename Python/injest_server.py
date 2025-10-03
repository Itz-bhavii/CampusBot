from flask import Flask,request,jsonify;
import uuid
import chromadb
app = Flask(__name__)
chromaClient = chromadb.HttpClient(host="localhost",port=8000)
collection = chromaClient.get_or_create_collection("practice_collection")

@app.route('/embed',methods = ['POST'])
def addText():
    uniqueId = str(uuid.uuid4())
    content = request.get_json()
    collection.add(
        ids=[uniqueId],
        documents=[content["text"]]
    )
    sendThis = {"text":content["text"]}
    return jsonify(sendThis)

@app.route("/embed",methods = ['GET'])
def getAll():
    list = collection.get(include=["documents"])
    list = list["documents"]
    return jsonify(list)

app.run(debug=True)
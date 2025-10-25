import os
import logging
import chromadb
import pytesseract
import logging.config
from typing import List
from google import genai
from common import clients
from fastapi import FastAPI
from dotenv import load_dotenv
from pydantic import BaseModel,Field
from logging_config import LOGGING_CONFIG
from sentence_transformers.cross_encoder import CrossEncoder


class QuerryResponse(BaseModel):
    message : str

class QuerryRequest(BaseModel):
    question : str
    chatHistory : List[str] = Field(default_factory=list)

class HealthyResponse(BaseModel):
    status : str

logging.config.dictConfig(LOGGING_CONFIG)
logger = logging.getLogger(__name__)

load_dotenv()
API_KEY = os.getenv("API_KEY")
pytesseract.pytesseract.tesseract_cmd = r'C:/Program Files/Tesseract-OCR/tesseract.exe'


try:
    if not API_KEY:
        logger.critical("API_KEY value not set")
        raise ValueError("API_KEY not set")
    #flask
    # app = Flask(__name__)

    #fastapi
    app = FastAPI()
    #loadingModels
    model = clients.getModel()
    modelCrossEncoder = CrossEncoder('cross-encoder/ms-marco-MiniLM-L-6-v2')
    googleClient = genai.Client(api_key=API_KEY)
    #chroma client
    chromaClient = chromadb.HttpClient(host="localhost",port=8000)
    # chromaClient.delete_collection("practice_collection")
    collection = chromaClient.get_or_create_collection(name="practice_collection",embedding_function=model)

except Exception as e:
    logger.critical("Failed during application initialization.", exc_info=True)
    exit(1)


@app.post("/querry")
def getQuerry(requestBody : QuerryRequest):
    question = requestBody.question
    chatHistory = requestBody.chatHistory

    if not question:
        return {"error ":"question not received"}

    logger.info("Received /querry request.", extra={'question': question, 'history_length': len(chatHistory)})

    standalone_question = question
    if chatHistory:
        formatted_history = "\n".join([f"{msg}" for msg in chatHistory])

        condense_prompt = f"""Given the following conversation history and a follow-up question, rephrase the follow-up question to be a standalone question that can be understood without the chat history.

        Chat History:
        {formatted_history}

        Follow-up Question: {question}

        Standalone Question:"""
        
        # print(condense_prompt)
        response = googleClient.models.generate_content(
            model="gemini-2.5-flash",
            contents=[condense_prompt]
        )
        standalone_question = response.text.strip()
        logger.info(f"Generated standalone question: {standalone_question}")

    expandedQuerries = getAlternateQuestions(standalone_question)

    results = collection.query(
        query_texts=expandedQuerries,
        n_results=5
    )
    uniqueAns = set()
    for bigList in results["documents"]:
        for data in bigList:
            uniqueAns.add(data)
    uniqueAns = list(uniqueAns)

    dataForCrossEncoder = uniqueAns
    sentencePairs = [[standalone_question,doc] for doc in dataForCrossEncoder]

    scores = modelCrossEncoder.predict(sentencePairs)
    scoredDocs = list(zip(scores,dataForCrossEncoder))
    scoredDocs.sort(reverse=True)
    topDocs = [doc for score , doc in scoredDocs[:2]]


    retrieved_context = "\n\n".join(topDocs)
    logger.info("Extracted matching results from ChromaDB.")

    final_prompt = f"""You are a helpful assistant. Answer the following question based ONLY on the provided context. If the context does not contain the answer, say "I do not have enough information to answer that question."

    Context:
    {retrieved_context}

    Question: {standalone_question}

    Answer:"""

    # print(final_prompt)
    logger.info("Calling final generation model.")
    final_response = googleClient.models.generate_content(
        model="gemini-2.5-flash",
        contents=[final_prompt]
    )
    logger.info("Final response generated.")
    print(question)
    print(final_response.text)

    return QuerryResponse(message=final_response.text.strip()) 


@app.get("/health")
def healthChecker():
    healthyResponse = HealthyResponse(status="Healthy")
    return healthyResponse



def getAlternateQuestions(standalone_question : str) -> list:
    querryExpansionPrompt = f"""
    Given the following user question, generate 4 alternative ways of asking the same thing.
    The queries should be diverse and cover different phrasings. Include the original question in the list and dont add any hint that it is the original question.

    Original Question: "{standalone_question}"

    Alternative Queries:
    1. {standalone_question}
    2. ...
    3. ...
    4. ...
    5. ...
    """

    expandedQuerryRaw = googleClient.models.generate_content(
        model="gemini-2.5-flash",
        contents=querryExpansionPrompt
    )

    questions = list(expandedQuerryRaw.text.strip().split("\n\n"))
    return questions

# if(__name__== "__main__"):
#     app.run(debug=True)
# @app.route("/querry",methods=['POST'])
# def getQuerry():
#     content = request.get_json()
#     question = content["question"]
#     chatHistory = content["chatHistory"]
#     print(question)
#     print(chatHistory)
#     if not question or not chatHistory:
#         return jsonify({"error": "Missing request body"}), 400
#     logger.info("Received /querry request.", extra={'question': question})
    
#     prompt = f"generate an single standalone question with the context provided. Context: [{chatHistory},{question}]"

#     modifiedQuestion = googleClient.models.generate_content(
#         model = "gemini-2.0-flash",
#         contents= prompt
#     )

#     print(modifiedQuestion.text)
#     result = collection.query(
#         query_texts=[modifiedQuestion.text],
#         n_results= 3
#     )
#     logger.info("Extracted The Matching Results")

#     prompt = f"Using only the provided context, answer the question. Context: [{result['documents']}]. Question: [{modifiedQuestion.text}]"

#     logger.info("Calling Model")
#     response = googleClient.models.generate_content(
#         model="gemini-2.0-flash",
#         contents=[prompt]
#     )
#     logger.info("Response Generated")

#     ans = {
#         "message":response.text
#     }
#     return jsonify(ans)




# @app.route("/ingest-image",methods = ['POST'])
# def getImage():
#     content = request.get_json()
#     imagePath = content["path"]
#     if not imagePath:
#         logger.error("image path not received")
#         return jsonify({"error": "Missing 'path' in request body"}), 400

#     logger.info("Path Extracted Successfully")
#     image = Image.open(imagePath)
#     imageDataText = pytesseract.image_to_string(image)
#     logger.info("Image Data Extracted Successfully")
#     extractAndStoreText(imageDataText) 
#     textToReturn = {
#         "content" : "Data Extracted Successfully"
#     }
#     return jsonify(textToReturn)



# @app.route('/ingest',methods = ['POST'])
# def addText():
#     content = request.get_json()
#     fileNameWithPath = content["path"]
#     if not fileNameWithPath:
#         logger.error("image path not received")
#         return jsonify({"error": "Missing 'path' in request body"}), 400
#     logger.info("Extracted Path")
#     textToReturn = getFileDataAndExtract(fileNameWithPath)

#     return jsonify(textToReturn)



# @app.route("/embed",methods = ['GET'])
# def getAll():
#     list = collection.get(include=["documents"])
#     list = list["documents"]
#     logger.info("Extracted Text")
#     return jsonify(list)

import os
import logging
import chromadb
import logging.config
from google import genai
from dotenv import load_dotenv
from campusbot_common import clients
from models.QuerryResponse import QuerryResponse
from campusbot_common.campus_logger import LOGGING_CONFIG
from sentence_transformers.cross_encoder import CrossEncoder


logging.config.dictConfig(LOGGING_CONFIG)
logger = logging.getLogger(__name__)

load_dotenv()
API_KEY = os.getenv("API_KEY")

try:
    if not API_KEY:
        logger.critical("API_KEY value not set")
        raise ValueError("API_KEY not set")
    #flask
    # app = Flask(__name__)

    #fastapi
    #loadingModels
    model = clients.getModel()
    modelCrossEncoder = CrossEncoder('cross-encoder/ms-marco-MiniLM-L-6-v2')
    googleClient = genai.Client(api_key=API_KEY)
    #chroma client
    chromaClient = chromadb.HttpClient(host="chromadb",port=8000)
    # chromaClient.delete_collection("practice_collection")
    collection = chromaClient.get_or_create_collection(name="practice_collection",embedding_function=model)

except Exception as e:
    logger.critical("Failed during application initialization.", exc_info=True)
    exit(1)

def getQuestionAndHistory(question,chatHistory):

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
    return QuerryResponse(message=final_response.text.strip())


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
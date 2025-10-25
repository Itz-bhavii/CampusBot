import logging.config
from fastapi import APIRouter
from logging_config import LOGGING_CONFIG
from querry_service.models.QuerryRequest import QuerryRequest 
from querry_service.services.chat_service import getQuestionAndHistory

router = APIRouter()

logging.config.dictConfig(LOGGING_CONFIG)
logger = logging.getLogger(__name__)

@router.post("/querry")
def getQuerry(requestBody : QuerryRequest):
    question = requestBody.question
    chatHistory = requestBody.chatHistory

    if not question:
        return {"error ":"question not received"}

    logger.info("Received /querry request.", extra={'question': question, 'history_length': len(chatHistory)})

    
    logger.info("Final response generated.")
    print(question)
    finalResponse = getQuestionAndHistory(question,chatHistory)

    return finalResponse
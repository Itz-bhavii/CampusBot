import logging.config
from fastapi import APIRouter
from campusbot.common.campus_logger import LOGGING_CONFIG
from ..models.QueryRequest import QueryRequest 
from ..services.chat_service import getQuestionAndHistory

router = APIRouter()

logging.config.dictConfig(LOGGING_CONFIG)
logger = logging.getLogger(__name__)

@router.post("/query")
def getQuery(requestBody : QueryRequest):
    question = requestBody.question
    chatHistory = requestBody.chatHistory

    if not question:
        return {"error ":"question not received"}

    logger.info("Received /query request.", extra={'question': question, 'history_length': len(chatHistory)})

    
    logger.info("Final response generated.")
    print(question)
    finalResponse = getQuestionAndHistory(question,chatHistory)

    return finalResponse
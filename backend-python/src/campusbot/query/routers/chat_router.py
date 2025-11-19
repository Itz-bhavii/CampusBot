"""
Chat API router for handling query requests.
Defines the /query endpoint that Spring Boot calls for AI answers.

REQUEST FLOW:
Spring Boot → POST /query → This router → chat_service.py → Gemini API → Response
"""

import logging.config
from fastapi import APIRouter
from campusbot.common.campus_logger import LOGGING_CONFIG
from ..models.QueryRequest import QueryRequest 
from ..services.chat_service import getQuestionAndHistory

# Create FastAPI router for chat endpoints
router = APIRouter()

# Configure logging
logging.config.dictConfig(LOGGING_CONFIG)
logger = logging.getLogger(__name__)

@router.post("/query")
def getQuery(requestBody : QueryRequest):
    """
    Main query endpoint - handles AI question answering requests.
    
    COMPLETE REQUEST FLOW:
    1. Spring Boot ChatMessageService sends POST request
    2. Request body contains:
       - question: current user question (string)
       - chatHistory: previous messages in conversation (list of strings)
    3. This endpoint validates question exists
    4. Calls chat_service.getQuestionAndHistory() which:
       a. Reformulates question using chat history (if any)
       b. Searches ChromaDB for relevant document chunks
       c. Ranks results using cross-encoder
       d. Generates answer using Gemini with retrieved context
    5. Returns QueryResponse with AI-generated answer
    6. Spring Boot receives response and returns to user
    
    REQUEST EXAMPLE:
    POST /query
    {
        "question": "How does RAG work?",
        "chatHistory": [
            "What is AI?",
            "AI is artificial intelligence...",
            "What is machine learning?",
            "ML is a subset of AI..."
        ]
    }
    
    RESPONSE EXAMPLE:
    {
        "message": "RAG (Retrieval Augmented Generation) works by..."
    }
    
    WHY CHAT HISTORY:
    Allows follow-up questions without repeating context:
    User: "What is CampusBot?"
    AI: "CampusBot is a chatbot..."
    User: "How does it work?" ← needs history to know "it" = CampusBot
    
    Args:
        requestBody: QueryRequest model with question and chatHistory
    
    Returns:
        QueryResponse: Contains AI-generated answer in message field
        Error dict: If question missing
    """
    # Extract question and chat history from request
    question = requestBody.question
    chatHistory = requestBody.chatHistory

    # Validate question exists
    if not question:
        return {"error ":"question not received"}

    # Log incoming request for monitoring
    logger.info("Received /query request.", extra={'question': question, 'history_length': len(chatHistory)})

    # Process question and generate AI response
    logger.info("Final response generated.")
    print(question)
    finalResponse = getQuestionAndHistory(question,chatHistory)

    return finalResponse
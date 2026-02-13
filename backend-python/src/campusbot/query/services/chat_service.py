"""
Core AI question answering service using RAG (Retrieval Augmented Generation).
Implements multi-stage pipeline for accurate, context-aware responses.

RAG ARCHITECTURE:
1. Question Reformulation: Converts follow-up questions to standalone questions
2. Query Expansion: Generates alternative phrasings for better retrieval
3. Vector Search: Finds relevant document chunks in ChromaDB
4. Re-ranking: Uses cross-encoder to select best chunks
5. Answer Generation: Sends question + context to Gemini API

WHY RAG:
- Pure LLM: limited knowledge, hallucinates, outdated information
- RAG: retrieves actual documents, grounds responses in facts, up-to-date
- Example: "What are CS department office hours?" → retrieves from uploaded PDFs

MODELS USED:
- Embedding: all-MiniLM-L6-v2 (converts text to vectors)
- Re-ranking: cross-encoder/ms-marco-MiniLM-L-6-v2 (precise relevance scoring)
- Generation: Gemini 2.5 Flash (fast AI text generation)
"""

import os
import logging
import chromadb
import logging.config
# import google.generativeai as genai
from dotenv import load_dotenv
from campusbot.common import clients
from ..models.QueryResponse import QueryResponse
from campusbot.common.campus_logger import LOGGING_CONFIG
from sentence_transformers.cross_encoder import CrossEncoder

from langchain_ollama import OllamaLLM

logging.config.dictConfig(LOGGING_CONFIG)
logger = logging.getLogger(__name__)

# Load environment variables from .env file
load_dotenv()
# API_KEY = os.getenv("API_KEY")  # Gemini API key

# ===== INITIALIZATION =====
try:
    # Validate API key exists
    if not API_KEY:
        logger.critical("API_KEY value not set")
        raise ValueError("API_KEY not set")

    # Load embedding model (same model used during ingestion)
    # Ensures query vectors match document vectors
    model = clients.getModel()
    
    # Load cross-encoder for re-ranking retrieved results
    # Cross-encoder is more accurate than bi-encoder for relevance scoring
    # Scores question-document pairs directly (slower but more precise)
    modelCrossEncoder = CrossEncoder('cross-encoder/ms-marco-MiniLM-L-6-v2')
    
    # Configure Gemini API
    # genai.configure(api_key=API_KEY)
    # Note: 'gemini-2.5-flash' may auto-resolve to available version


    #replacing gemini with ollama
    # generation_model = genai.GenerativeModel("gemini-2.5-flash")

    generation_model = OllamaLLM(model="qwen2.5:7b-instruct-q4_K_M",base_url="http://host.docker.internal:11434")
    
    # Connect to ChromaDB vector database
    chromaClient = chromadb.HttpClient(host="chromadb",port=8000)
    
    # Get collection containing all indexed documents
    # Same collection name as ingestion worker
    collection = chromaClient.get_or_create_collection(
        name="practice_collection",
        embedding_function=model  # Auto-embeds queries during search
    )

except Exception as e:
    logger.critical("Failed during application initialization.", exc_info=True)
    exit(1)

def getQuestionAndHistory(question,chatHistory):
    """
    Main RAG pipeline - processes question and generates contextual answer.
    
    COMPLETE 5-STAGE PIPELINE:
    
    STAGE 1: QUESTION REFORMULATION
    Problem: Follow-up questions lack context
    Example conversation:
      User: "What is CampusBot?"
      AI: "CampusBot is a chatbot..."
      User: "How does it work?" ← "it" is ambiguous without history
    
    Solution: Reformulate using chat history
    - If no history: use question as-is
    - If history exists: ask Gemini to create standalone question
    - Result: "How does CampusBot work?" (clear without context)
    
    STAGE 2: QUERY EXPANSION
    Problem: User's wording might not match document wording
    Example: User asks "How do I register?" but doc says "enrollment process"
    
    Solution: Generate alternative phrasings
    - "How do I register for courses?"
    - "What is the course enrollment process?"
    - "Steps to sign up for classes"
    - "Registration procedure"
    - Searches with all variations increase recall
    
    STAGE 3: VECTOR SEARCH
    Process: Search ChromaDB for similar chunks
    - Each alternative query → converted to 384-dim vector
    - ChromaDB finds top 5 chunks per query using cosine similarity
    - Collects all results and deduplicates
    
    Example:
    Query vector: [0.23, -0.45, 0.67, ...]
    Chunk 1: [0.21, -0.43, 0.69, ...] similarity = 0.95 ✓
    Chunk 2: [0.88, 0.12, -0.34, ...] similarity = 0.32 ✗
    
    STAGE 4: RE-RANKING WITH CROSS-ENCODER
    Problem: Bi-encoder (sentence transformers) fast but less accurate
    Solution: Cross-encoder scores question-document pairs precisely
    
    Process:
    - Takes all retrieved chunks
    - Scores each against standalone question
    - Sorts by score (highest = most relevant)
    - Selects top 2 chunks for context
    
    Why cross-encoder is better:
    - Bi-encoder: encodes question and doc separately, compares vectors
    - Cross-encoder: processes question+doc together, learns interaction
    - Example: can understand negation, subtle semantic differences
    
    STAGE 5: ANSWER GENERATION WITH GEMINI
    Process: Send question + retrieved context to Gemini
    
    Prompt structure:
    ```
    You are a helpful assistant. Answer ONLY based on provided context.
    If context doesn't contain answer, say "I don't have enough information."
    
    Context:
    [Top 2 most relevant document chunks]
    
    Question: [Standalone reformulated question]
    
    Answer:
    ```
    
    Why this works:
    - Context grounds AI in facts (prevents hallucination)
    - Instruction limits AI to context (prevents making things up)
    - Standalone question is clear (no ambiguous pronouns)
    
    Args:
        question: User's current question (str)
        chatHistory: List of previous messages in conversation (list of str)
                     Format: [user_msg1, ai_msg1, user_msg2, ai_msg2, ...]
    
    Returns:
        QueryResponse: Contains AI-generated answer in message field
    """
    
    # STAGE 1: Question Reformulation
    standalone_question = question  # Default to original
    
    if chatHistory:
        # Format chat history for context
        # Each message on new line for clarity
        formatted_history = "\n".join([f"{msg}" for msg in chatHistory])

        # Prompt Gemini to reformulate question using history
        condense_prompt = f"""Given the following conversation history and a follow-up question, rephrase the follow-up question to be a standalone question that can be understood without the chat history.

        Chat History:
        {formatted_history}

        Follow-up Question: {question}

        Standalone Question:"""
        
        # Call Gemini to reformulate
        # response = generation_model.generate_content(
        #     contents=[condense_prompt]
        # )
        response = generation_model.invoke(condense_prompt)

        # standalone_question = response.text.strip()
        standalone_question = response.strip()
        logger.info(f"Generated standalone question: {standalone_question}")

    # STAGE 2: Query Expansion
    # Generate alternative phrasings for better retrieval
    expandedQueries = getAlternateQuestions(standalone_question)

    # STAGE 3: Vector Search in ChromaDB
    # Search with all query variations, get top 5 per query
    results = collection.query(
        query_texts=expandedQueries,  # List of query strings
        n_results=5   # Top 5 results per query
    )
    
    # Deduplicate results (same chunk might match multiple queries)
    uniqueAns = set()
    for bigList in results["documents"]:
        for data in bigList:
            uniqueAns.add(data)
    uniqueAns = list(uniqueAns)

    # STAGE 4: Re-ranking with Cross-Encoder
    # Create question-document pairs for scoring
    dataForCrossEncoder = uniqueAns
    sentencePairs = [[standalone_question,doc] for doc in dataForCrossEncoder]

    # Score each pair (how relevant is doc to question?)
    scores = modelCrossEncoder.predict(sentencePairs)
    
    # Combine scores with documents and sort by relevance
    scoredDocs = list(zip(scores,dataForCrossEncoder))
    scoredDocs.sort(reverse=True)  # Highest score first
    
    # Select top 2 most relevant chunks
    topDocs = [doc for score , doc in scoredDocs[:2]]

    # Combine top chunks into context string
    retrieved_context = "\n\n".join(topDocs)
    logger.info("Extracted matching results from ChromaDB.")

    # STAGE 5: Generate Answer with Gemini
    # Create prompt with context and question
    final_prompt = f"""You are a helpful assistant. Answer the following question based ONLY on the provided context. If the context does not contain the answer, say "I do not have enough information to answer that question."

    Context:
    {retrieved_context}

    Question: {standalone_question}

    Answer:"""

    # Call Gemini for final answer generation
    logger.info("Calling final generation model.")
    # final_response = generation_model.generate_content(
    #     contents=[final_prompt]
    # )

    final_response = generation_model.invoke(final_prompt)
    
    # Return answer wrapped in response model
    return QueryResponse(message=final_response.strip())


def getAlternateQuestions(standalone_question : str) -> list:
    """
    Generates alternative phrasings of a question for query expansion.
    
    PURPOSE:
    Increases recall in vector search by covering different ways to ask same thing.
    
    EXAMPLE:
    Input: "How do I register for courses?"
    Output:
    1. "How do I register for courses?"
    2. "What is the course enrollment process?"
    3. "Steps to sign up for classes"
    4. "How can I enroll in courses?"
    5. "Course registration procedure"
    
    WHY THIS HELPS:
    - User's exact wording might not match document wording
    - Different phrasings cover more semantic space
    - More queries = higher chance of finding relevant chunks
    - Example: "register" vs "enroll" vs "sign up" - all mean same thing
    
    PROCESS:
    1. Prompt Gemini to generate 4 alternatives
    2. Include original question in list (total 5 queries)
    3. Gemini generates diverse phrasings
    4. Split response into list of questions
    5. Return all 5 for vector search
    
    Args:
        standalone_question: The reformulated standalone question
    
    Returns:
        list: 5 alternative phrasings of the question (including original)
    """
    # Create prompt for query expansion
    queryExpansionPrompt = f"""
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

    # Call Gemini to generate alternatives
    # expandedQueryRaw = generation_model.generate_content(
    #     contents=queryExpansionPrompt
    # )
    
    expandedQueryRaw = generation_model.invoke(queryExpansionPrompt)

    # Parse response into list of questions
    # Assumes Gemini returns questions separated by double newlines
    questions = list(expandedQueryRaw.strip().split("\n\n"))
    
    return questions
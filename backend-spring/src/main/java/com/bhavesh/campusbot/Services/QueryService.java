package com.bhavesh.campusbot.Services;

import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.stereotype.Service;
import org.springframework.web.client.RestTemplate;

import com.bhavesh.campusbot.DTO.MessageDTO;
import com.bhavesh.campusbot.DTO.QueryDTO;

/**
 * Service responsible for communicating with the Python AI Query Service.
 * Acts as a bridge between Spring Boot backend and Python FastAPI service.
 * 
 * ARCHITECTURE OVERVIEW:
 * - Spring Boot handles: user auth, database, file storage, business logic
 * - Python Service handles: AI/ML, vector search, LLM integration
 * - This service connects them via HTTP REST calls
 * 
 * QUERY FLOW:
 * 1. User asks a question through chat interface
 * 2. ChatMessageService prepares QueryDTO with question + chat history
 * 3. This service sends HTTP POST to Python query-service
 * 4. Python service:
 *    a. Searches ChromaDB vector database for relevant document chunks
 *    b. Retrieves top matching content
 *    c. Sends question + context + chat history to Gemini API
 *    d. Receives AI-generated response
 * 5. This service receives MessageDTO with AI's answer
 * 6. Returns to ChatMessageService which saves and returns to user
 */
@Service
public class QueryService {

    // RestTemplate for making synchronous HTTP requests to external services
    @Autowired
    private RestTemplate restTemplate;

    /**
     * Sends user's question and chat history to Python AI service and returns AI's response.
     * 
     * COMMUNICATION DETAILS:
     * - Endpoint: http://query-service:8000/query
     * - Method: POST
     * - Request body: QueryDTO containing question and chat history array
     * - Response: MessageDTO containing AI's answer
     * 
     * SERVICE NAME RESOLUTION:
     * "query-service" is a Docker Compose service name defined in docker-compose.yml
     * Docker's internal DNS resolves this to the Python container's IP address
     * Port 8000 is where the Python FastAPI app listens
     * 
     * WHAT HAPPENS IN PYTHON SERVICE:
     * 1. Receives QueryDTO
     * 2. Converts question to vector embedding using sentence transformers
     * 3. Performs similarity search in ChromaDB to find relevant document chunks
     * 4. Retrieves top N most relevant chunks
     * 5. Constructs prompt with: user question + retrieved context + chat history
     * 6. Calls Gemini API with constructed prompt
     * 7. Receives AI response
     * 8. Returns as MessageDTO
     * 
     * @param query QueryDTO containing the user's question and conversation history
     * @return MessageDTO containing the AI-generated answer
     */
    public MessageDTO sendQueryToPython(QueryDTO query){
        // Docker Compose service name - DNS resolves to Python container
        String url = "http://query-service:8000/query";
        // POST request with QueryDTO body, expect MessageDTO response
        return restTemplate.postForObject(url, query, MessageDTO.class);
    }   
}

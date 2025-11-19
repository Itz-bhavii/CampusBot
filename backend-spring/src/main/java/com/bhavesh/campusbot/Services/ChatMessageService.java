package com.bhavesh.campusbot.Services;

import java.util.ArrayList;
import java.util.List;
import java.util.UUID;

import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.stereotype.Service;

import com.bhavesh.campusbot.DTO.MessageDTO;
import com.bhavesh.campusbot.DTO.QueryDTO;
import com.bhavesh.campusbot.Entities.ChatMessage;
import com.bhavesh.campusbot.Repositorys.ChatMessageRepository;
import com.bhavesh.campusbot.Utils.UuidUtils;

/**
 * Service layer for handling chat messages between users and the AI assistant.
 * 
 * FLOW OVERVIEW:
 * 1. User sends a message through the API
 * 2. This service creates a ChatMessage entity from the user's message
 * 3. Checks if this is a new conversation or existing conversation by looking at conversationId
 * 4. If existing conversation, retrieves previous messages to provide context to the AI
 * 5. Sends the question + chat history to Python Query Service (AI service)
 * 6. Receives AI's response and saves it to database
 * 7. Returns AI's response back to the user
 * 
 * This service acts as a bridge between the user interface and the AI backend.
 */
@Service
public class ChatMessageService {
    
    // Constant identifier for messages coming from the AI assistant
    final String SENDER = "AI";

    // Repository for database operations on chat messages
    @Autowired
    private ChatMessageRepository chatMessageRepository;

    // Service to communicate with Python AI backend
    @Autowired
    private QueryService queryService;

    /**
     * Saves a chat message to the database.
     * This is used to persist both user messages and AI responses.
     * 
     * @param message The ChatMessage entity to save
     */
    public void saveChat(ChatMessage message){
        chatMessageRepository.save(message);
    }

    /**
     * MAIN PROCESSING METHOD - This is the heart of the chat flow.
     * 
     * COMPLETE FLOW:
     * 1. Takes user's message (MessageDTO) and converts it to database entity (ChatMessage)
     * 2. Checks if conversationId exists:
     *    - If empty/null: Creates new conversation with new UUID, starts with empty chat history
     *    - If exists: Retrieves all previous messages in this conversation for context
     * 3. Saves the user's message to database
     * 4. Prepares QueryDTO containing the current question + full chat history
     * 5. Sends QueryDTO to Python backend which:
     *    - Uses chat history to understand context
     *    - Searches ChromaDB vector database for relevant information
     *    - Generates AI response using Gemini API
     * 6. Receives AI's response (MessageDTO)
     * 7. Attaches the same conversationId to AI's response
     * 8. Converts AI's response to ChatMessage and saves it to database
     * 9. Returns AI's response to the user
     * 
     * @param query The user's message wrapped in MessageDTO
     * @param sender Username of the person who sent the message
     * @return MessageDTO containing AI's response with conversationId attached
     */
    public MessageDTO processAndSendData(MessageDTO query, String sender){
        // Step 1: Convert user's message DTO to database entity
        ChatMessage message = createChatMessageFromQuery(query, sender);

        List<String> recentMessages;
        // Step 2: Check if this is a new or existing conversation
        if(UuidUtils.isUUidEmpty(message.getConversationId())){
            // New conversation: generate new UUID and start with empty history
            message.setConversationId(UUID.randomUUID());
            recentMessages = new ArrayList<>();
        } else {
            // Existing conversation: load all previous messages for context
            recentMessages = retrieveRecentMessages(message.getConversationId());
        }
        
        // Step 3: Save user's message to database
        saveChat(message);
        
        // Step 4: Prepare data transfer object for Python AI service
        QueryDTO queryDTO = new QueryDTO();
        queryDTO.setQuestion(query.getMessage());
        queryDTO.setChatHistory(recentMessages);  // Full conversation context

        // Step 5: Send question + history to Python backend and get AI response
        MessageDTO ans =  queryService.sendQueryToPython(queryDTO);
        
        // Step 6: Attach the same conversationId to maintain conversation thread
        ans.setConversationId(message.getConversationId());
        
        // Step 7: Convert AI's response to database entity
        ChatMessage chatMessage = createChatMessageFromQuery(ans, SENDER);
        
        // Step 8: Save AI's response to database
        saveChat(chatMessage);
        
        System.out.println(ans.getMessage());
        System.out.println(ans.getConversationId());
        
        // Step 9: Return AI's response to user
        return ans;
    }

    /**
     * Converts a MessageDTO (data transfer object) to ChatMessage entity (database model).
     * This is needed because DTOs are used for API communication while entities are used for database storage.
     * 
     * @param content The MessageDTO containing message text and conversationId
     * @param sender The username or identifier of who sent this message (user or "AI")
     * @return ChatMessage entity ready to be saved to database
     */
    public ChatMessage createChatMessageFromQuery(MessageDTO content,String sender){
        ChatMessage message = new ChatMessage();
        message.setUuid(UUID.randomUUID());  // Unique identifier for this specific message
        message.setSender(sender);  // Who sent it (username or "AI")
        message.setMessage(content.getMessage());  // The actual message text
        message.setConversationId(content.getConversationId());  // Which conversation thread this belongs to

        return message;
    }

    /**
     * Retrieves all messages in a conversation, ordered by timestamp (oldest first).
     * This gives us the chronological order of the conversation.
     * 
     * @param conversationId The UUID identifying the conversation thread
     * @return List of ChatMessage entities ordered by timestamp ascending
     */
    public List<ChatMessage> getAllMessagesByConversationId(UUID conversationId){
        return chatMessageRepository.findByConversationIdOrderByTimestampAsc(conversationId);
    }

    /**
     * Extracts just the message text from all messages in a conversation.
     * This creates the "chat history" array that's sent to the AI for context.
     * 
     * EXAMPLE: If conversation has 4 messages:
     * User: "What is AI?"
     * AI: "AI stands for Artificial Intelligence..."
     * User: "How does it work?"
     * AI: "AI works by..."
     * 
     * This method returns: ["What is AI?", "AI stands for...", "How does it work?", "AI works by..."]
     * 
     * @param conversationId The UUID identifying the conversation thread
     * @return List of strings containing just the message text in chronological order
     */
    public List<String> retrieveRecentMessages(UUID conversationId){
        List<String> chatHistory = new ArrayList<>();
        // Get all messages in this conversation
        List<ChatMessage> chatMessageList = getAllMessagesByConversationId(conversationId);

        // Extract just the text from each message
        for(ChatMessage chatMessage : chatMessageList){
            chatHistory.add(chatMessage.getMessage());
        }

        return chatHistory;
    }

}
    
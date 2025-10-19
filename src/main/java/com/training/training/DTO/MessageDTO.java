package com.training.training.DTO;

import java.util.UUID;

public class MessageDTO {
    private UUID conversationId;
    private String message;

    
    public UUID getConversationId() {
        return conversationId;
    }

    public void setConversationId(UUID conversationId) {
        this.conversationId = conversationId;
    }

    
    public String getMessage() {
        return message;
    }

    public void setMessage(String message) {
        this.message = message;
    }



}

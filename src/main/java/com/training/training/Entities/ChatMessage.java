package com.training.training.Entities;


import java.time.LocalDateTime;
import java.util.UUID;

import org.hibernate.annotations.CreationTimestamp;

import jakarta.persistence.Entity;
import jakarta.persistence.Id;

@Entity
public class ChatMessage {
    @Id
    private UUID uuid;
    private UUID conversationId;
    private String sender;
    private String message;
    @CreationTimestamp
    private LocalDateTime timestamp;

    public LocalDateTime gettimestamp() {
        return timestamp;
    }
    public void settimestamp(LocalDateTime timestamp) {
        this.timestamp = timestamp;
    }
    public UUID getUuid() {
        return uuid;
    }
    public void setUuid(UUID uuid) {
        this.uuid = uuid;
    }
    public UUID getConversationId() {
        return conversationId;
    }
    public void setConversationId(UUID conversationId) {
        this.conversationId = conversationId;
    }
    public String getSender() {
        return sender;
    }
    public void setSender(String sender) {
        this.sender = sender;
    }
    public String getMessage() {
        return message;
    }
    public void setMessage(String message) {
        this.message = message;
    }

}

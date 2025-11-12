package com.bhavesh.campusbot.DTO;

import java.util.List;

public class QueryDTO {
    String question;
    List<String> chatHistory;   

    
    public String getQuestion() {
        return question;
    }
    public void setQuestion(String question) {
        this.question = question;
    }
    public List<String> getChatHistory() {
        return chatHistory;
    }
    public void setChatHistory(List<String> chatHistory) {
        this.chatHistory = chatHistory;
    }
    
}

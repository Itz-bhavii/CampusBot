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

@Service
public class ChatMessageService {
    
    final String SENDER = "AI";

    @Autowired
    private ChatMessageRepository chatMessageRepository;

    @Autowired
    private QueryService queryService;

    public void saveChat(ChatMessage message){
        chatMessageRepository.save(message);
    }

    public MessageDTO processAndSendData(MessageDTO query, String sender){
        ChatMessage message = createChatMessageFromQuery(query, sender);

        List<String> recentMessages;
        if(UuidUtils.isUUidEmpty(message.getConversationId())){
            message.setConversationId(UUID.randomUUID());
            recentMessages = new ArrayList<>();
        } else {
            recentMessages = retrieveRecentMessages(message.getConversationId());
        }
        saveChat(message);
        QueryDTO queryDTO = new QueryDTO();
        queryDTO.setQuestion(query.getMessage());
        queryDTO.setChatHistory(recentMessages);

        MessageDTO ans =  queryService.sendQueryToPython(queryDTO);
        ans.setConversationId(message.getConversationId());
        ChatMessage chatMessage = createChatMessageFromQuery(ans, SENDER);
        saveChat(chatMessage);
        System.out.println(ans.getMessage());
        System.out.println(ans.getConversationId());
        return ans;

    }

    public ChatMessage createChatMessageFromQuery(MessageDTO content,String sender){
        
        ChatMessage message = new ChatMessage();
        message.setUuid(UUID.randomUUID());
        message.setSender(sender);
        message.setMessage(content.getMessage());
        message.setConversationId(content.getConversationId());

        return message;
    }

    public List<ChatMessage> getAllMessagesByConversationId(UUID conversationId){
        return chatMessageRepository.findByConversationIdOrderByTimestampAsc(conversationId);
    }

    public List<String> retrieveRecentMessages(UUID conversationId){
        List<String> chatHistory = new ArrayList<>();
        List<ChatMessage> chatMessageList = getAllMessagesByConversationId(conversationId);

        for(ChatMessage chatMessage : chatMessageList){
            chatHistory.add(chatMessage.getMessage());
        }


        return chatHistory;
    }

}
    
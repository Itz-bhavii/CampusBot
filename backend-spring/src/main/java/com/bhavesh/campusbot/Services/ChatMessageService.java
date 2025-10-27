package com.bhavesh.campusbot.Services;

import java.util.ArrayList;
import java.util.List;
import java.util.UUID;

import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.stereotype.Service;

import com.bhavesh.campusbot.DTO.MessageDTO;
import com.bhavesh.campusbot.DTO.QuerryDTO;
import com.bhavesh.campusbot.Entities.ChatMessage;
import com.bhavesh.campusbot.Repositorys.ChatMessageRepository;
import com.bhavesh.campusbot.Utils.UuidUtils;

@Service
public class ChatMessageService {
    
    final String SENDER = "AI";

    @Autowired
    private ChatMessageRepository chatMessageRepository;

    @Autowired
    private QuerryService querryService;

    public void saveChat(ChatMessage message){
        chatMessageRepository.save(message);
    }

    public MessageDTO processAndSendData(MessageDTO querry, String sender){
        ChatMessage message = createChatMessageFromQuerry(querry, sender);

        List<String> recentMessages;
        if(UuidUtils.isUUidEmpty(message.getConversationId())){
            message.setConversationId(UUID.randomUUID());
            recentMessages = new ArrayList<>();
        } else {
            recentMessages = retrieveRecentMessages(message.getConversationId());
        }
        saveChat(message);
        QuerryDTO querryDTO = new QuerryDTO();
        querryDTO.setQuestion(querry.getMessage());
        querryDTO.setChatHistory(recentMessages);

        MessageDTO ans =  querryService.sendQuerryToPython(querryDTO);
        ans.setConversationId(message.getConversationId());
        ChatMessage chatMessage = createChatMessageFromQuerry(ans, SENDER);
        saveChat(chatMessage);
        System.out.println(ans.getMessage());
        System.out.println(ans.getConversationId());
        return ans;

    }

    public ChatMessage createChatMessageFromQuerry(MessageDTO content,String sender){
        
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
    
package com.training.training.Services;

import java.util.List;
import java.util.UUID;

import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.stereotype.Service;
import org.springframework.web.client.RestTemplate;

import com.training.training.DTO.AnswerDTO;
import com.training.training.DTO.MessageDTO;
import com.training.training.DTO.QuerryDTO;
import com.training.training.Entities.ChatMessage;


@Service
public class QuerryService {


    @Autowired
    private RestTemplate restTemplate;

    
    public MessageDTO sendQuerryToFlask(QuerryDTO querry){
        String url = "http://127.0.0.1:5000/querry";
        return restTemplate.postForObject(url, querry, MessageDTO.class);
    }   
}

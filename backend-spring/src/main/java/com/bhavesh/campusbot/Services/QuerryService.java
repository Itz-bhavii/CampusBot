package com.bhavesh.campusbot.Services;

import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.stereotype.Service;
import org.springframework.web.client.RestTemplate;

import com.bhavesh.campusbot.DTO.MessageDTO;
import com.bhavesh.campusbot.DTO.QuerryDTO;


@Service
public class QuerryService {


    @Autowired
    private RestTemplate restTemplate;

    
    public MessageDTO sendQuerryToPython(QuerryDTO querry){
        String url = "http://query-service:8000/query";
        return restTemplate.postForObject(url, querry, MessageDTO.class);
    }   
}

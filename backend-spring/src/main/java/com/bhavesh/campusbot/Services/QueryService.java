package com.bhavesh.campusbot.Services;

import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.stereotype.Service;
import org.springframework.web.client.RestTemplate;

import com.bhavesh.campusbot.DTO.MessageDTO;
import com.bhavesh.campusbot.DTO.QueryDTO;


@Service
public class QueryService {


    @Autowired
    private RestTemplate restTemplate;

    
    public MessageDTO sendQueryToPython(QueryDTO query){
        String url = "http://query-service:8000/query";
        return restTemplate.postForObject(url, query, MessageDTO.class);
    }   
}

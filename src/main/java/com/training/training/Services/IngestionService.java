package com.training.training.Services;

import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.http.ResponseEntity;
import org.springframework.stereotype.Service;
import org.springframework.web.client.RestTemplate;

import com.training.training.Entities.SampleTextForFlask;

@Service
public class IngestionService {
    @Autowired
    private RestTemplate restTemplate;

    public String sendDataToFlask(SampleTextForFlask text){
        String url = "http://127.0.0.1:5000/embed";
        restTemplate.postForObject(url,text,SampleTextForFlask.class);
        return "status:success";
    }
}

package com.training.training.Services;

import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.stereotype.Service;
import org.springframework.web.client.RestTemplate;
import org.springframework.web.multipart.MultipartFile;

import com.training.training.DTO.AnswerDTO;
import com.training.training.Entities.Querry;

@Service
public class QuerryService {
    @Autowired
    private RestTemplate restTemplate;

    
    public String sendQuerryToFlask(Querry querry){
        String url = "http://127.0.0.1:5000/querry";
        AnswerDTO ans = restTemplate.postForObject(url, querry, AnswerDTO.class);
        if(ans == null) return "";
        return ans.getAnswer();
    }
}

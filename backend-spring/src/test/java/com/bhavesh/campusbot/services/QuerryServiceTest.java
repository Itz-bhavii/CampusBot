package com.bhavesh.campusbot.services;

import static org.mockito.Mockito.when;

import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.extension.ExtendWith;
import org.mockito.InjectMocks;
import org.mockito.Mock;
import org.mockito.junit.jupiter.MockitoExtension;
import org.springframework.web.client.RestTemplate;

import com.bhavesh.campusbot.DTO.AnswerDTO;
import com.bhavesh.campusbot.DTO.MessageDTO;
import com.bhavesh.campusbot.Services.QuerryService;

@ExtendWith(MockitoExtension.class)
public class QuerryServiceTest {
    @Mock
    RestTemplate restTemplate;

    @InjectMocks
    QuerryService querryService;

    @Test
    void sendQuerryToFlaskShouldPass(){
        MessageDTO querry = new MessageDTO();
        querry.setMessage("what is java");

        AnswerDTO expectedAns = new AnswerDTO();
        expectedAns.setAnswer("Java is a programming language");

        when(restTemplate.postForObject("http://127.0.0.1:5000/querry", querry, AnswerDTO.class)).thenReturn(expectedAns);

        // String ans = querryService.sendQuerryToFlask(querry);
        // Assertions.assertEquals(expectedAns.getAnswer(), ans);

    }
}

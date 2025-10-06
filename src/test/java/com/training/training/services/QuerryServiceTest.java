package com.training.training.services;

import static org.mockito.Mockito.when;

import org.junit.jupiter.api.Assertions;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.extension.ExtendWith;
import org.mockito.InjectMocks;
import org.mockito.Mock;
import org.mockito.junit.jupiter.MockitoExtension;
import org.springframework.web.client.RestTemplate;

import com.training.training.DTO.AnswerDTO;
import com.training.training.Entities.Querry;
import com.training.training.Services.QuerryService;

@ExtendWith(MockitoExtension.class)
public class QuerryServiceTest {
    @Mock
    RestTemplate restTemplate;

    @InjectMocks
    QuerryService querryService;

    @Test
    void sendQuerryToFlaskShouldPass(){
        Querry querry = new Querry();
        querry.setQuestion("what is java");

        AnswerDTO expectedAns = new AnswerDTO();
        expectedAns.setAnswer("Java is a programming language");

        when(restTemplate.postForObject("http://127.0.0.1:5000/querry", querry, AnswerDTO.class)).thenReturn(expectedAns);

        String ans = querryService.sendQuerryToFlask(querry);
        Assertions.assertEquals(expectedAns.getAnswer(), ans);

    }
}

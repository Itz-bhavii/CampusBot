package com.training.training.Services;

import org.springframework.amqp.rabbit.core.RabbitTemplate;
import org.springframework.stereotype.Service;

import com.training.training.Config.RabbitMQConfig;

record CustomMessage(String mssgId,String mssgContent){}

@Service
public class SenderMessageMQService {
    final RabbitTemplate rabbitTemplate;

    public SenderMessageMQService(RabbitTemplate rabbitTemplate){
        this.rabbitTemplate = rabbitTemplate;
    }

    public void sendMessage(CustomMessage messageToSend){
        rabbitTemplate.convertAndSend(RabbitMQConfig.EXCHANGE_NAME,RabbitMQConfig.ROUTING_KEY,messageToSend);
    }
}

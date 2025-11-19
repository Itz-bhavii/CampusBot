package com.bhavesh.campusbot.Listeners;

import org.springframework.amqp.rabbit.annotation.RabbitListener;
import org.springframework.stereotype.Component;

import com.bhavesh.campusbot.Config.RabbitMQConfig;
import com.bhavesh.campusbot.DTO.AcknowledgementDTO;

@Component
public class AcknowledgementListener {

    @RabbitListener(queues = RabbitMQConfig.ACKNOWLEDGEMENT_QUEUE)
    public void onAcknowledgement(AcknowledgementDTO ack){
        System.out.println(ack.isProcessed());
        System.out.println(ack.getDocumentId());
        if(ack.isProcessed()){
            System.out.println(ack.getDocumentName() + " file processed successfully");
        } else {
            System.out.println(ack.getDocumentName() + " file cannot be processed");
        }
    }
}

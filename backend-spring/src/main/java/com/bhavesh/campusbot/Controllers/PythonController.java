package com.bhavesh.campusbot.Controllers;

import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RequestParam;
import org.springframework.web.bind.annotation.RestController;
import org.springframework.web.multipart.MultipartFile;

import com.bhavesh.campusbot.DTO.MessageDTO;
import com.bhavesh.campusbot.Services.ChatMessageService;
import com.bhavesh.campusbot.Services.IngestionService;


@RestController
@RequestMapping("/api")
public class PythonController {

    
    final String SENDER = "USER";

    @Autowired
    private IngestionService ingestionService;


    @Autowired
    private ChatMessageService chatMessageService;


    @PostMapping("/ingest")
    public ResponseEntity<HttpStatus> addDataInPython(@RequestParam("file") MultipartFile file){
        if(ingestionService.getFile(file)){
            return new ResponseEntity<>(HttpStatus.ACCEPTED);
        }
        else{
            return new ResponseEntity<>(HttpStatus.BAD_REQUEST);
        }
    }

    @PostMapping("/ingest-image")
    public String sendImageToPython(@RequestParam("image") MultipartFile image){
        return ingestionService.getImage(image).getcontent();
    }

    @PostMapping("/chat")
    public MessageDTO sendQuestion(@RequestBody MessageDTO query){
        return chatMessageService.processAndSendData(query,SENDER);
        // return queryService.sendQueryToFlask(query);

    }

    

}

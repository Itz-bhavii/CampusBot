package com.training.training.Controllers;

import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.http.HttpStatus;
import org.springframework.http.HttpStatusCode;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RequestParam;
import org.springframework.web.bind.annotation.ResponseBody;
import org.springframework.web.bind.annotation.RestController;
import org.springframework.web.multipart.MultipartFile;

import com.training.training.Entities.Querry;
import com.training.training.Services.IngestionService;
import com.training.training.Services.QuerryService;


@RestController
@RequestMapping("/api")
public class PythonController {

    @Autowired
    private IngestionService ingestionService;

    @Autowired
    private QuerryService querryService;


    @PostMapping("/ingest")
    public ResponseEntity addDataInFlask(@RequestParam("file") MultipartFile file){
        if(ingestionService.getFile(file)){
            return new ResponseEntity<>(HttpStatus.ACCEPTED);
        }
        else{
            return new ResponseEntity<>(HttpStatus.BAD_REQUEST);
        }
    }

    @PostMapping("/ingest-image")
    public String sendImageToFlask(@RequestParam("image") MultipartFile image){
        return ingestionService.getImage(image).getcontent();
    }

    @PostMapping("/chat")
    public String sendQuestion(@RequestBody Querry querry){
        return querryService.sendQuerryToFlask(querry);

    }

}

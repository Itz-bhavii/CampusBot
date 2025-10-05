package com.training.training.Controllers;

import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RequestParam;
import org.springframework.web.bind.annotation.RestController;
import org.springframework.web.multipart.MultipartFile;

import com.training.training.DTO.ContentDTO;
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
    public String addDataInFlask(@RequestParam("file") MultipartFile file){
        return ingestionService.getFile(file).getcontent();
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

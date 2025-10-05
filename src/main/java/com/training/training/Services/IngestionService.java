package com.training.training.Services;

import java.io.File;
import java.io.FileWriter;
import java.nio.file.Files;
import java.nio.file.Path;
import java.nio.file.Paths;

import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.http.ResponseEntity;
import org.springframework.stereotype.Service;
import org.springframework.web.client.RestTemplate;
import org.springframework.web.multipart.MultipartFile;

import com.training.training.Entities.ContentOfFileFromFlask;

@Service
public class IngestionService {
    @Autowired
    private RestTemplate restTemplate;

    public ContentOfFileFromFlask getFile(MultipartFile receivedFile){
        String uploadUrl = "D:/Temp/uploads/";
        File directory = new File(uploadUrl);
        if(!directory.exists()){
            directory.mkdir();
        }
        Path path = Paths.get(uploadUrl + receivedFile.getOriginalFilename());
        try{
            Files.write(path, receivedFile.getBytes());
        } catch(Exception e) {
            System.out.println(e);
        }

        Object filePathObj = new Object(){
            public String filePath = path.toString();
        };
        
        String url = "http://127.0.0.1:5000/embed";
        ContentOfFileFromFlask content = restTemplate.postForObject(url,filePathObj,ContentOfFileFromFlask.class);
        return content;
    }
}

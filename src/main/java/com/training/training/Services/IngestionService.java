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

import com.training.training.DTO.ContentDTO;
import com.training.training.DTO.PathDTO;

@Service
public class IngestionService {
    @Autowired
    private RestTemplate restTemplate;

    public ContentDTO getFile(MultipartFile receivedFile){
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

        PathDTO pathDTO = new PathDTO(path.toString());
        
        String url = "http://127.0.0.1:5000/ingest";
        ContentDTO content = restTemplate.postForObject(url,pathDTO,ContentDTO.class);
        return content;
    }


    public ContentDTO getImage(MultipartFile image){
        String uploadLoc = "D:/Temp/uploads/";
        File directory = new File(uploadLoc);
        if(!directory.exists()){
            directory.mkdir();
        }
        Path path = Paths.get(uploadLoc + image.getOriginalFilename());
        try{
            Files.write(path, image.getBytes());
        } catch(Exception e){
            System.out.println(e);
        }

        PathDTO pathDTO = new PathDTO(path.toString());

        String url = "http://127.0.0.1:5000/ingest-image";
        ContentDTO content = restTemplate.postForObject(url,pathDTO, ContentDTO.class);

        return content;
    }
}

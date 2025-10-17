package com.training.training.Services;


import java.util.UUID;

import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.stereotype.Service;
import org.springframework.web.client.RestTemplate;
import org.springframework.web.multipart.MultipartFile;

import com.training.training.DTO.ContentDTO;
import com.training.training.DTO.PathDTO;

@Service
public class IngestionService {
    @Autowired
    private RestTemplate restTemplate;

    @Autowired
    private FileStorageService fileStorageService;

    @Autowired
    private SenderMessageMQService senderMessageMQService;

    public boolean getFile(MultipartFile receivedFile){
        String uuid = UUID.randomUUID().toString();
        String storedFileName = fileStorageService.storeFileAndReturnPath(receivedFile);
        senderMessageMQService.sendMessage(new CustomMessage(uuid,storedFileName));
        


        // PathDTO pathDTO = new PathDTO(storedFilePath);
        
        // String url = "http://127.0.0.1:5000/ingest";
        // ContentDTO content = restTemplate.postForObject(url,pathDTO,ContentDTO.class);
        return true;
    }


    public ContentDTO getImage(MultipartFile image){
        String storedFilePath = fileStorageService.storeFileAndReturnPath(image);

        PathDTO pathDTO = new PathDTO(storedFilePath);

        String url = "http://127.0.0.1:5000/ingest-image";
        ContentDTO content = restTemplate.postForObject(url,pathDTO, ContentDTO.class);

        return content;
    }
}

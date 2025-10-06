package com.training.training.Services;

import java.io.File;
import java.nio.file.Files;
import java.nio.file.Path;
import java.nio.file.Paths;

import org.springframework.stereotype.Service;
import org.springframework.web.multipart.MultipartFile;

@Service
public class FileStorageService {
    
    public String storeFileAndReturnPath(MultipartFile receivedFile){
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

        return path.toString();
    }
}

package com.training.training.Services;


import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.stereotype.Service;
import org.springframework.web.multipart.MultipartFile;

import io.minio.MinioClient;
import io.minio.ObjectWriteResponse;
import io.minio.PutObjectArgs;

@Service
public class FileStorageService {
    
    @Autowired
    private MinioClient minioClient;

    public String storeFileAndReturnPath(MultipartFile receivedFile){

        try{
                ObjectWriteResponse savedObject = minioClient.putObject(
                    PutObjectArgs.builder()
                    .bucket("campusbot-ingestion-vault")
                    .object(receivedFile.getOriginalFilename())
                    .stream(receivedFile.getInputStream(), receivedFile.getSize(),-1)
                    .contentType(receivedFile.getContentType())
                    .build()
                );

                return savedObject.object();
            } catch (Exception e){
                System.out.println(e.getMessage());
            }
            
            return "";
            // System.out.println(savedObject.bucket());
            // System.out.println("--");
            // System.out.println(savedObject.etag());
            // System.out.println("--");
            // System.out.println("--");
            // System.out.println(savedObject.region());
            // System.out.println("--");
            // System.out.println(savedObject.versionId());
            // System.out.println("--");
            // System.out.println(savedObject.headers());
            // System.out.println("--");
            // System.out.println(savedObject.getClass());
            // System.out.println("--");
            // savedObject.object();


        // String uploadUrl = "D:/Temp/uploads/";
        // File directory = new File(uploadUrl);
        // if(!directory.exists()){
        //     directory.mkdir();
        // }
        // Path path = Paths.get(uploadUrl + receivedFile.getOriginalFilename());
        // try{
        //     Files.write(path, receivedFile.getBytes());
        // } catch(Exception e) {
        //     System.out.println(e);
        // }

        // return path.toString();
    }
}

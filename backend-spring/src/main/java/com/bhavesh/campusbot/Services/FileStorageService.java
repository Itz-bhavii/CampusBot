package com.bhavesh.campusbot.Services;


import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.stereotype.Service;
import org.springframework.web.multipart.MultipartFile;

import io.minio.MinioClient;
import io.minio.ObjectWriteResponse;
import io.minio.PutObjectArgs;

/**
 * Service for storing uploaded files to MinIO object storage.
 * MinIO is an S3-compatible storage system used to store documents.
 * 
 * ARCHITECTURE:
 * Instead of storing files in local filesystem, we use MinIO because:
 * - Scalable: handles large files and many files easily
 * - Distributed: can run on multiple servers
 * - S3-compatible: can swap with AWS S3 in production
 * - Accessible: Python workers can access files from same MinIO instance
 * 
 * STORAGE FLOW:
 * 1. User uploads file via REST API
 * 2. Spring Boot receives MultipartFile
 * 3. This service streams file to MinIO bucket "campusbot-files"
 * 4. Returns object name (filename) for reference
 * 5. Filename is sent to Python ingestion worker via RabbitMQ
 * 6. Python worker downloads file from MinIO, processes it, extracts text
 */
@Service
public class FileStorageService {
    
    // MinIO client configured with endpoint, credentials from application.properties
    @Autowired
    private MinioClient minioClient;

    /**
     * Stores uploaded file in MinIO object storage and returns the object name.
     * 
     * STORAGE DETAILS:
     * - Bucket: "campusbot-files" (must be created beforehand or via initialization)
     * - Object name: Original filename from upload
     * - Content is streamed directly without loading entire file into memory (efficient for large PDFs)
     * 
     * PROCESS:
     * 1. Receives MultipartFile from controller
     * 2. Creates PutObjectArgs with:
     *    - bucket name: where to store
     *    - object name: filename to use in bucket
     *    - stream: file content as InputStream
     *    - size: file size for MinIO metadata
     *    - contentType: MIME type (e.g., "application/pdf")
     * 3. MinIO client uploads file to storage
     * 4. Returns object name on success
     * 5. Returns empty string on failure (caller should handle this)
     * 
     * INTEGRATION:
     * After storing here, the object name is:
     * - Sent to RabbitMQ queue for Python worker
     * - Python worker uses same MinIO credentials to download file
     * - File is processed and text extracted for AI
     * 
     * @param receivedFile The uploaded file from HTTP request
     * @return Object name (filename) if successful, empty string if failed
     */
    public String storeFileInMinioAndReturnPath(MultipartFile receivedFile){

        try{
                // Upload file to MinIO using streaming (memory efficient)
                ObjectWriteResponse savedObject = minioClient.putObject(
                    PutObjectArgs.builder()
                    .bucket("campusbot-files")  // Bucket name in MinIO
                    .object(receivedFile.getOriginalFilename())  // Use original filename as object key
                    .stream(receivedFile.getInputStream(), receivedFile.getSize(),-1)  // Stream file content
                    .contentType(receivedFile.getContentType())  // Preserve MIME type
                    .build()
                );

                // Return the object name for reference (used to download later)
                return savedObject.object();
            } catch (Exception e){
                System.out.println(e.getMessage());
            }
            
            // Return empty string on failure
            return "";
    }
}

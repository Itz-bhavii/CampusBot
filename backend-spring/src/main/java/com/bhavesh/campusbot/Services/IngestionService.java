package com.bhavesh.campusbot.Services;


import java.time.Instant;

import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.security.core.context.SecurityContextHolder;
import org.springframework.stereotype.Service;
import org.springframework.web.client.RestTemplate;
import org.springframework.web.multipart.MultipartFile;

import com.bhavesh.campusbot.DTO.ContentDTO;
import com.bhavesh.campusbot.DTO.PathDTO;
import com.bhavesh.campusbot.Entities.Document;

/**
 * Service that handles document ingestion into the CampusBot AI system.
 * Coordinates file upload, storage, duplicate detection, and notification to Python workers.
 * 
 * COMPLETE INGESTION FLOW:
 * 1. User uploads document (PDF, DOCX, TXT) through REST API
 * 2. This service generates unique documentId using SHA-256 hash
 * 3. Checks if file already exists (duplicate detection)
 * 4. If new: stores file in MinIO object storage
 * 5. Saves document metadata to PostgreSQL database
 * 6. Sends message to RabbitMQ queue notifying Python worker
 * 7. Python ingestion worker receives message
 * 8. Worker downloads file from MinIO
 * 9. Worker extracts text, chunks it, generates embeddings
 * 10. Worker stores embeddings in ChromaDB vector database
 * 11. Worker sends acknowledgement back via RabbitMQ
 * 12. Document is now searchable by AI query service
 * 
 * This service is the orchestrator for steps 1-6.
 */
@Service
public class IngestionService {
    // For making HTTP calls (legacy code - not currently used)
    @Autowired
    private RestTemplate restTemplate;

    // Service to store files in MinIO
    @Autowired
    private FileStorageService fileStorageService;

    // Service to send messages to RabbitMQ
    @Autowired
    private SenderMessageMQService senderMessageMQService;

    // Service for generating document IDs and managing metadata
    @Autowired
    private DocumentIdService documentIdService;

    /**
     * Main ingestion method - processes uploaded file and triggers AI indexing.
     * 
     * STEP-BY-STEP FLOW:
     * 1. DUPLICATE DETECTION:
     *    - Generates SHA-256 hash of file content (deterministic ID)
     *    - Checks if this documentId already exists in database
     *    - If duplicate: returns false immediately (no processing)
     * 
     * 2. FILE STORAGE:
     *    - Stores file to MinIO object storage bucket "campusbot-files"
     *    - MinIO is S3-compatible distributed storage
     *    - Returns the stored filename (object name in MinIO)
     * 
     * 3. METADATA PERSISTENCE:
     *    - Extracts current logged-in username from Spring Security context
     *    - Creates Document entity with:
     *      * documentId: SHA-256 hash
     *      * originalFilename: what user named the file
     *      * uploadedBy: username from security context
     *      * uploadedAt: current timestamp
     *      * processed: false (will be updated to true after Python worker finishes)
     *    - Saves to PostgreSQL database
     * 
     * 4. WORKER NOTIFICATION:
     *    - Creates CustomMessage containing documentId and filename
     *    - Sends message to RabbitMQ queue "documents.queue"
     *    - Python ingestion worker is listening on this queue
     *    - Worker will download file and process it asynchronously
     * 
     * @param receivedFile The uploaded file from HTTP multipart request
     * @return true if ingestion initiated successfully, false if duplicate or failure
     */
    public boolean getFile(MultipartFile receivedFile){
        // Step 1: Generate content-based unique ID
        String documentId = documentIdService.generateId(receivedFile);

        // Step 2: Check for duplicates - reject if already exists
        if(documentIdService.isDuplicate(documentId)){
            System.out.println("File already Exists");
            return false;
        }

        // Step 3: Store file in MinIO object storage
        String storedFileName = fileStorageService.storeFileInMinioAndReturnPath(receivedFile);

        // Step 4: Get username of currently logged-in user from security context
        String loginedUsername = SecurityContextHolder.getContext().getAuthentication().getName();
        
        // Step 5: Create and save document metadata to database
        Document doc = new Document(documentId,receivedFile.getOriginalFilename(),loginedUsername,Instant.now(),false);
        documentIdService.save(doc);

        // Step 6: Notify Python worker via RabbitMQ to process this document
        boolean isMessageSended = senderMessageMQService.sendMessage(new CustomMessage(documentId,storedFileName));
        
        return isMessageSended;
    }


    /**
     * Legacy method for image ingestion (not currently used in main flow).
     * Originally designed for direct HTTP call to Python service.
     * Kept for potential future use case.
     * 
     * @param image Uploaded image file
     * @return ContentDTO containing extracted content
     */
    public ContentDTO getImage(MultipartFile image){
        String storedFilePath = fileStorageService.storeFileInMinioAndReturnPath(image);

        PathDTO pathDTO = new PathDTO(storedFilePath);

        String url = "http://127.0.0.1:5000/ingest-image";
        ContentDTO content = restTemplate.postForObject(url,pathDTO, ContentDTO.class);

        return content;
    }
}

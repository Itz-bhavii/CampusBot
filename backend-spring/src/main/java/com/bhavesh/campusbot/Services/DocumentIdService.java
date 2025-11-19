package com.bhavesh.campusbot.Services;

import java.io.InputStream;
import java.security.MessageDigest;
import java.security.NoSuchAlgorithmException;

import org.springframework.stereotype.Service;
import org.springframework.web.multipart.MultipartFile;

import com.bhavesh.campusbot.Entities.Document;
import com.bhavesh.campusbot.Repositorys.DocumentIdRepository;

/**
 * Service for generating unique document IDs and managing document metadata.
 * Uses SHA-256 hashing to create content-based IDs for duplicate detection.
 * 
 * PURPOSE:
 * - Prevents duplicate file uploads by identifying identical files
 * - Generates deterministic IDs: same file content = same ID
 * - Tracks document metadata in database
 * 
 * HOW IT WORKS:
 * When a file is uploaded, this service:
 * 1. Computes SHA-256 hash of the entire file content
 * 2. Converts hash to hexadecimal string (documentId)
 * 3. Checks if this ID already exists in database
 * 4. If duplicate: rejects upload
 * 5. If unique: saves document metadata and proceeds
 */
@Service
public class DocumentIdService {

    // Repository for storing document metadata in database
    private final DocumentIdRepository documentIdRepository;

    public DocumentIdService(DocumentIdRepository documentIdRepository){
        this.documentIdRepository = documentIdRepository;
    }

    /**
     * Saves document metadata to the database.
     * Stores information like documentId, filename, uploader, upload date, etc.
     * 
     * @param document The Document entity containing metadata
     * @return true if save successful, false otherwise
     */
    public boolean save(Document document){
        return documentIdRepository.save(document) != null;
    }
    
    /**
     * Generates a unique document ID using SHA-256 hash of file content.
     * This creates a deterministic ID - same file will always produce same ID.
     * 
     * HASHING PROCESS:
     * 1. Reads file content in 8KB chunks (efficient for large files)
     * 2. Continuously updates SHA-256 hash with each chunk
     * 3. After reading entire file, computes final hash (32 bytes)
     * 4. Converts hash bytes to 64-character hexadecimal string
     * 
     * DUPLICATE DETECTION:
     * If two users upload the exact same PDF, both will generate identical IDs.
     * This allows system to detect and reject duplicates automatically.
     * 
     * @param file The uploaded file (MultipartFile from Spring)
     * @return 64-character hex string representing the file's SHA-256 hash
     * @throws RuntimeException if SHA-256 algorithm not available or file read fails
     */
    public String generateId(MultipartFile file){
        try{
            // Initialize SHA-256 message digest algorithm
            MessageDigest md = MessageDigest.getInstance("SHA-256");
            InputStream inputStream = file.getInputStream();
            // 8KB buffer for reading file in chunks (memory efficient)
            byte[] buffer = new byte[8192];
            int noOfBytesReaded;
            // Read file in chunks and update hash continuously
            while((noOfBytesReaded = inputStream.read(buffer)) != -1){
                md.update(buffer,0,noOfBytesReaded);
            }

            // Compute final hash value (32 bytes)
            byte[] hashBytes =  md.digest();
            // Convert to hexadecimal string for storage
            return bytesToHex(hashBytes);
            
        } catch (NoSuchAlgorithmException e){
            throw new RuntimeException("No such algorithm",e);
        } catch (Exception e){
            throw new RuntimeException("Exception occured while generating document id",e);
        }
    }

    /**
     * Converts byte array to hexadecimal string representation.
     * Each byte becomes 2 hex characters (00 to FF).
     * 
     * EXAMPLE:
     * Input bytes: [255, 0, 128]
     * Output string: "FF0080"
     * 
     * For SHA-256 (32 bytes), output will be 64 hex characters.
     * 
     * @param hashBytes The byte array to convert
     * @return Uppercase hexadecimal string
     */
    public String bytesToHex(byte[] hashBytes){
        StringBuilder hex = new StringBuilder();
        for(byte b : hashBytes){
            // %02X formats byte as 2-digit uppercase hex (with leading zero if needed)
            hex.append(String.format("%02X",b));
        }

        return hex.toString();
    }

    /**
     * Checks if a document with given ID already exists in the database.
     * Used to detect duplicate file uploads before processing.
     * 
     * USAGE IN FLOW:
     * 1. User uploads file
     * 2. System generates documentId from file content
     * 3. Calls this method to check if ID exists
     * 4. If true: file is duplicate, reject upload
     * 5. If false: file is new, proceed with storage
     * 
     * @param documentId The SHA-256 hash ID to check
     * @return true if document exists, false if new
     */
    public boolean isDuplicate(String documentId){
        return documentIdRepository.existsById(documentId);
    }
}

package com.bhavesh.campusbot.Services;

import java.util.Map;
import java.util.UUID;
import java.util.concurrent.CompletableFuture;
import java.util.concurrent.ConcurrentHashMap;
import java.util.concurrent.ExecutionException;
import java.util.concurrent.TimeUnit;
import java.util.concurrent.TimeoutException;

import org.springframework.amqp.rabbit.connection.CorrelationData;
import org.springframework.amqp.rabbit.core.RabbitTemplate;
import org.springframework.stereotype.Service;
import com.bhavesh.campusbot.Config.RabbitMQConfig;

/**
 * Data structure to hold message details sent to RabbitMQ.
 * - documentId: SHA-256 hash of the document (unique identifier)
 * - mssgContent: filename in MinIO where the actual file is stored
 */
record CustomMessage(String documentId,String mssgContent){}

/**
 * Service for sending messages to RabbitMQ with publisher confirmation.
 * Implements reliable message delivery with acknowledgement tracking.
 * 
 * MESSAGING ARCHITECTURE:
 * Spring Boot (this service) → RabbitMQ → Python Ingestion Worker
 * 
 * PURPOSE:
 * When a file is uploaded and stored in MinIO, we need to notify the Python worker
 * to download and process it. This service sends that notification reliably.
 * 
 * PUBLISHER CONFIRMS PATTERN:
 * RabbitMQ can acknowledge when it has received and persisted a message.
 * This service waits for that acknowledgement to ensure message delivery.
 * 
 * HOW IT WORKS:
 * 1. Creates message with unique correlation ID
 * 2. Stores CompletableFuture in map (indexed by correlation ID)
 * 3. Sends message to RabbitMQ
 * 4. Thread blocks waiting for confirmation
 * 5. RabbitMQ processes message and sends confirm/nack callback
 * 6. Callback completes the CompletableFuture (unblocks thread)
 * 7. Returns success/failure to caller
 * 
 * This ensures we know if message reached RabbitMQ successfully.
 */
@Service
public class SenderMessageMQService {
    // RabbitTemplate: Spring's abstraction for RabbitMQ operations
    final RabbitTemplate rabbitTemplate;
    
    // Thread-safe map storing pending confirmations
    // Key: correlation ID (UUID), Value: CompletableFuture that completes when RabbitMQ confirms
    private final Map<String, CompletableFuture<Boolean>> pendingConfirms = new ConcurrentHashMap<>();
    
    // Timeout for waiting for confirmation (5 seconds)
    private final long CONFIRM_TIMEOUT_MS = 5000L;

    /**
     * Constructor that initializes RabbitTemplate with publisher confirmation callback.
     * 
     * CALLBACK MECHANISM:
     * When RabbitMQ receives a message, it sends confirmation back to this application.
     * This callback is invoked when that confirmation arrives.
     * 
     * CALLBACK FLOW:
     * 1. Message is sent with correlation ID (e.g., "abc-123")
     * 2. Thread stores CompletableFuture in pendingConfirms map with key "abc-123"
     * 3. Thread blocks waiting for CompletableFuture to complete
     * 4. RabbitMQ processes message
     * 5. RabbitMQ sends confirmation with same correlation ID "abc-123"
     * 6. This callback is triggered with correlationData containing "abc-123"
     * 7. Callback retrieves the CompletableFuture from map
     * 8. Callback completes the future with ack=true or ack=false
     * 9. Original thread unblocks and returns result
     * 
     * PARAMETERS:
     * - correlationData: contains the unique ID we assigned to this message
     * - ack: true if RabbitMQ successfully received message, false if rejected
     * - cause: error message if ack=false
     * 
     * @param rabbitTemplate Spring's RabbitMQ template configured in RabbitMQConfig
     */
    public SenderMessageMQService(RabbitTemplate rabbitTemplate){
        this.rabbitTemplate = rabbitTemplate;
        
        // Set callback that runs when RabbitMQ confirms message receipt
        this.rabbitTemplate.setConfirmCallback((correlationData, ack, cause) -> {
                
            System.out.println("entered the callback function");
            
            // Validate correlation data exists
            if (correlationData == null || correlationData.getId() == null) {
                // Invalid confirmation - ignore it
                return;
            }
            
            // Extract the correlation ID we assigned during send
            String id = correlationData.getId();
            
            // Remove from pending map and get the future (atomic operation)
            // This ensures only one thread processes this confirmation
            CompletableFuture<Boolean> future = pendingConfirms.remove(id);
            System.out.println(future);
            
            if (future != null) {
                // Future exists - complete it with acknowledgement status
                // This unblocks the thread waiting in sendMessage() method
                future.complete(ack);
            } else {
                // Future not found - either timed out or duplicate confirm
                System.out.println("Confirm for unknown id=" + id + " ack=" + ack + " cause=" + cause);
            }
        });
    }

    /**
     * Sends message to RabbitMQ and waits for confirmation.
     * Returns true only if RabbitMQ successfully acknowledged receipt.
     * 
     * COMPLETE MESSAGE FLOW:
     * 1. Generate unique correlation ID for this message
     * 2. Create CompletableFuture to track confirmation
     * 3. Store future in pendingConfirms map (correlation ID → future)
     * 4. Send message to RabbitMQ with correlation data
     * 5. Current thread BLOCKS waiting for confirmation
     * 6. RabbitMQ receives message and sends confirmation
     * 7. Confirmation callback is invoked (see constructor)
     * 8. Callback completes the CompletableFuture
     * 9. This thread unblocks and returns result
     * 
     * RABBITMQ ROUTING:
     * - Exchange: "campusbot.exchange" (topic exchange)
     * - Routing Key: "documents.ingest" 
     * - Queue: "documents.queue" (bound to exchange with routing key)
     * - Consumer: Python ingestion worker listening on "documents.queue"
     * 
     * MESSAGE CONTENT:
     * CustomMessage contains:
     * - documentId: hash identifier
     * - mssgContent: filename in MinIO
     * 
     * Python worker receives this and:
     * 1. Downloads file from MinIO using filename
     * 2. Extracts text from document
     * 3. Chunks text into smaller pieces
     * 4. Generates embeddings for each chunk
     * 5. Stores in ChromaDB vector database
     * 6. Sends completion acknowledgement
     * 
     * @param messageToSend CustomMessage with documentId and filename
     * @return true if RabbitMQ confirmed receipt, false if rejected or error
     */
    public boolean sendMessage(CustomMessage messageToSend){
        // Step 1: Generate unique ID to correlate this message with its confirmation
        String id = UUID.randomUUID().toString();
        CorrelationData correlationData = new CorrelationData(id);

        // Step 2: Create future that will be completed when confirmation arrives
        CompletableFuture<Boolean> ackFuture = new CompletableFuture<>();
        
        // Step 3: Store in map so callback can find it
        // Both map and local variable point to SAME CompletableFuture object
        // When callback completes it, this thread's get() call will unblock
        pendingConfirms.put(id, ackFuture);

        // Step 4: Publish message to RabbitMQ
        // convertAndSend automatically serializes CustomMessage to JSON
        rabbitTemplate.convertAndSend(
            RabbitMQConfig.EXCHANGE_NAME,       // "campusbot.exchange"
            RabbitMQConfig.ROUTING_KEY_DOC,     // "documents.ingest"
            messageToSend,                       // CustomMessage payload
            correlationData                      // Correlation ID for tracking
        );

        try {
            // Step 5: BLOCK current thread waiting for confirmation
            // When callback calls future.complete(ack), this returns
            // Note: Timeout is commented out - thread waits indefinitely
            // Boolean ack = ackFuture.get(CONFIRM_TIMEOUT_MS, TimeUnit.MILLISECONDS);
            Boolean ack = ackFuture.get();
            
            // Step 6: Return true only if ack is true (message confirmed)
            return Boolean.TRUE.equals(ack);

        // Timeout handling (currently disabled)
        // } catch (TimeoutException te) {
        //     // Timeout: clean up map and treat as failure
        //     pendingConfirms.remove(id);
        //     return false;
            
        } catch (InterruptedException | ExecutionException e) {
            // Thread interrupted or execution failed - clean up and fail
            pendingConfirms.remove(id);
            return false;
        }
    }
}

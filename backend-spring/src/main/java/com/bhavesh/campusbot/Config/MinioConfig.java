package com.bhavesh.campusbot.Config;
import io.minio.MinioClient;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;

/**
 * Configuration class for MinIO object storage client.
 * MinIO is an S3-compatible distributed object storage system.
 * 
 * WHY MINIO:
 * - Stores uploaded documents (PDFs, DOCX, TXT files)
 * - S3-compatible API (can swap with AWS S3 easily)
 * - Both Spring Boot and Python workers can access same files
 * - Scalable and handles large files efficiently
 * 
 * ARCHITECTURE:
 * 1. User uploads file → Spring Boot
 * 2. Spring Boot stores file in MinIO bucket "campusbot-files"
 * 3. Spring Boot sends filename to RabbitMQ
 * 4. Python worker receives message
 * 5. Python worker downloads same file from MinIO using filename
 * 6. Worker processes and deletes from MinIO
 * 
 * This config creates the MinIO client used by FileStorageService.
 */
@Configuration
public class MinioConfig {

    // MinIO server URL - loaded from application.properties
    // Example: http://localhost:9000 or http://minio:9000 (in Docker)
    @Value("${minio.endpoint}")
    private String endpoint;

    // MinIO access key (like AWS access key)
    // Loaded from application.properties or environment variable
    @Value("${minio.access.key}")
    private String accessKey;

    // MinIO secret key (like AWS secret key)
    // Loaded from application.properties or environment variable
    @Value("${minio.secret.key}")
    private String secretKey;

    /**
     * Creates and configures MinIO client bean.
     * This client is used throughout the application for object storage operations.
     * 
     * CLIENT CAPABILITIES:
     * - Upload objects (putObject)
     * - Download objects (getObject)
     * - Delete objects (removeObject)
     * - List objects (listObjects)
     * - Create buckets (makeBucket)
     * 
     * CONNECTION DETAILS:
     * - Endpoint: where MinIO server is running
     * - Credentials: access key + secret key for authentication
     * - Thread-safe: single instance shared across services
     * 
     * CONFIGURATION SOURCE:
     * Properties are injected from:
     * 1. application.properties file, OR
     * 2. Environment variables (in Docker), OR
     * 3. System properties
     * 
     * Example properties:
     * minio.endpoint=http://localhost:9000
     * minio.access.key=minioadmin
     * minio.secret.key=minioadmin
     * 
     * @return Configured MinioClient ready for use
     */
    @Bean
    public MinioClient minioClient() {
        return MinioClient.builder()
                .endpoint(endpoint)                    // MinIO server URL
                .credentials(accessKey, secretKey)     // Authentication credentials
                .build();
    }
}
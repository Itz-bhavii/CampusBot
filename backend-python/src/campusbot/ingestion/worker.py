"""
Document Ingestion Worker for CampusBot.
Background service that processes uploaded documents and stores them in ChromaDB.

ARCHITECTURE ROLE:
This worker is the async processing engine that:
1. Listens to RabbitMQ queue for document upload notifications
2. Downloads files from MinIO object storage
3. Extracts text and metadata using parser.py
4. Generates embeddings and stores in ChromaDB vector database
5. Sends acknowledgement back to Spring Boot

COMPLETE SYSTEM FLOW:
User uploads PDF → Spring Boot stores in MinIO → Spring Boot sends message to RabbitMQ
→ THIS WORKER receives message → Downloads from MinIO → Parses document
→ Generates embeddings → Stores in ChromaDB → Sends ACK to Spring Boot

WHY ASYNC WORKER:
- Document processing is slow (parsing, embedding generation)
- Spring Boot shouldn't wait for processing to complete
- Worker can be scaled independently (multiple instances)
- If worker crashes, messages stay in queue (reliability)

RUNNING:
- Runs as long-lived process (typically in Docker container)
- Blocks waiting for RabbitMQ messages
- Processes one message at a time (or can be configured for parallel)
- Logs all operations for debugging
"""

import os
import re
import sys
import uuid
import boto3  # AWS SDK (MinIO is S3-compatible)
import tabula

# Flush print statements immediately for Docker log visibility
def log(message):
    """Helper function to log messages with immediate flush to stdout.
    Critical for Docker logs where buffering can hide messages."""
    print(f"[WORKER] {message}", flush=True)

log("=== INGESTION WORKER STARTING ===")
log("Importing parser module...")
from . import parser_ai  # Local parser module for document extraction
log("Parser module imported successfully")

import tempfile  # For temporary file storage during processing
import chromadb  # Vector database client
import pika  # RabbitMQ client library
import json
import pandas as pd
from campusbot.common import clients  # Shared embedding model client
from collections import defaultdict
from unstructured.partition.pdf import partition_pdf
from unstructured.partition.text import partition_text
from langchain_text_splitters import RecursiveCharacterTextSplitter
from unstructured.documents.elements import Title,NarrativeText,ListItem,Table
log("All imports successful")


# ===== INITIALIZATION SECTION =====
# Load environment variables and connect to all external services
# If any service fails to connect, worker exits immediately
try:
    log("Reading environment variables...")
    
    # RabbitMQ connection URL (AMQP protocol)
    # Format: amqp://username:password@host:port/vhost
    URL = os.environ.get("CLOUDAMQP_URL")
    
    # MinIO bucket configuration
    BUCKET_NAME = os.getenv("BUCKET_NAME")  # Where files are stored
    MINIO_ACCESS_KEY = os.getenv("MINIO_ACCESS_KEY")  # S3-style access key
    MINIO_SECRET_KEY = os.getenv("MINIO_SECRET_KEY")  # S3-style secret key
    MINIO_ENDPOINT_URL = os.getenv("MINIO_ENDPOINT_URL")  # MinIO server URL
    
    log(f"Environment variables loaded - CLOUDAMQP_URL: {URL[:20] if URL else 'None'}..., BUCKET: {BUCKET_NAME}, MINIO_ENDPOINT: {MINIO_ENDPOINT_URL}")

    # Validate all required environment variables are set
    # Missing variables = misconfiguration = exit immediately
    if not URL:
        raise ValueError("CLOUDAMQP_URL not set")
    if not BUCKET_NAME:
        raise ValueError("BUCKETNAME not set")
    if not MINIO_ACCESS_KEY:
        raise ValueError("MINIO_ACCESS_KEY not set")
    if not MINIO_SECRET_KEY:
        raise ValueError("MINIO_SECRET_KEY not set")
    if not MINIO_ENDPOINT_URL:
        raise ValueError("MINIO_ENDPOINT_URL not set")
    
    # ===== EMBEDDING MODEL INITIALIZATION =====
    # Load sentence transformer model for generating text embeddings
    # This converts text chunks into vector representations for semantic search
    log("Initializing embedding model...")
    model = clients.getModel()  # Returns embedding function (sentence-transformers)
    
    # ===== CHROMADB CONNECTION =====
    # Connect to ChromaDB vector database
    # ChromaDB stores document chunks as vectors for similarity search
    log("Connecting to ChromaDB...")
    chromaClient = chromadb.HttpClient(host="chromadb",port=8000)  # Docker service name
    
    # Get or create collection (like a table in traditional DB)
    # Collection stores vectors + metadata for all uploaded documents
    collection = chromaClient.get_or_create_collection(
        name="practice_collection",
        embedding_function=model  # Automatic embedding generation on add()
    )
    log("ChromaDB connected successfully")
    
    # ===== MINIO CONNECTION =====
    # Connect to MinIO using boto3 (AWS S3 SDK)
    # MinIO is S3-compatible, so we use AWS SDK
    log("Connecting to MinIO...")
    botoClient = boto3.client(
        "s3",
        endpoint_url = MINIO_ENDPOINT_URL,  # MinIO server (not AWS)
        aws_access_key_id=MINIO_ACCESS_KEY,
        aws_secret_access_key=MINIO_SECRET_KEY
    )
    log("MinIO connected successfully")

    # ===== RABBITMQ CONSTANTS =====
    # Must match configuration in Spring Boot's RabbitMQConfig.java
    DOCUMENT_QUEUE = "documents.queue"  # Queue for document notifications
    ACKNOWLEDGEMENT_QUEUE = "acknowledgements.queue"  # Queue for ACKs
    EXCHANGE_NAME = "main-exchange"  # Topic exchange for routing
    ROUTING_KEY_DOC = "campusbot.documents"  # Route to document queue
    ROUTING_KEY_ACK = "campusbot.acknowledgements"  # Route to ACK queue

    # ===== RABBITMQ CONNECTION =====
    # Connect to RabbitMQ message broker
    log("Connecting to RabbitMQ...")
    params = pika.URLParameters(URL)  # Parse AMQP URL
    connection = pika.BlockingConnection(params)  # Establish connection
    channel = connection.channel()  # Create channel for operations

    # Declare topic exchange (idempotent - safe to call multiple times)
    # Topic exchange routes messages based on routing keys
    channel.exchange_declare(exchange=EXCHANGE_NAME, exchange_type='topic', durable=True)
    log("RabbitMQ exchange declared")
    
    # Declare queues (durable = survive RabbitMQ restart)
    channel.queue_declare(queue=DOCUMENT_QUEUE, durable=True)
    channel.queue_declare(queue=ACKNOWLEDGEMENT_QUEUE, durable=True)

    # Bind document queue to exchange with routing key
    # Messages sent with ROUTING_KEY_DOC will arrive in DOCUMENT_QUEUE
    channel.queue_bind(queue=DOCUMENT_QUEUE, exchange=EXCHANGE_NAME, routing_key=ROUTING_KEY_DOC)
    log("Queue bound to exchange successfully")

except Exception as e:
    # Fatal error during initialization - cannot proceed
    # Print full traceback for debugging and exit
    log(f"FATAL: Failed to initialize worker: {e}")
    import traceback
    traceback.print_exc()
    exit(1)


# ===== MESSAGE PROCESSING CALLBACK =====
def callback(ch,method,properties,body):
    """
    RabbitMQ message callback - invoked when a new message arrives in the queue.
    This is the main processing function that handles document ingestion.
    
    TRIGGER:
    Automatically called by RabbitMQ when message arrives in DOCUMENT_QUEUE.
    
    COMPLETE MESSAGE FLOW:
    1. Spring Boot uploads file to MinIO
    2. Spring Boot sends message to RabbitMQ: {"documentId": "abc123", "mssgContent": "file.pdf"}
    3. RabbitMQ delivers message to this worker
    4. THIS CALLBACK is invoked with message body
    5. Worker downloads file from MinIO
    6. Worker parses and stores in ChromaDB
    7. Worker sends ACK to RabbitMQ (message processed)
    8. Worker sends completion message back to Spring Boot
    
    MESSAGE FORMAT (JSON):
    {
        "documentId": "SHA256_hash_of_file",
        "mssgContent": "filename_in_minio.pdf"
    }
    
    ACKNOWLEDGEMENT MODES:
    - basic_ack: Message processed successfully, remove from queue
    - basic_nack(requeue=False): Failed permanently, remove from queue (dead letter)
    - basic_nack(requeue=True): Failed temporarily, re-queue for retry
    
    ERROR HANDLING:
    - JSON decode error: ACK (malformed message, don't retry)
    - Processing error: ACK (log error, don't block queue)
    - Success: ACK + send completion notification
    
    Args:
        ch: RabbitMQ channel object
        method: Delivery method (contains delivery_tag for ACK)
        properties: Message properties (headers, etc.)
        body: Message body (bytes) - JSON string
    """
    log("Callback invoked - message received")

    try:
        # Step 1: Decode and parse JSON message
        jsonString = body.decode()  # bytes → string
        bodyData = json.loads(jsonString)  # string → dict
        log(f"Message received: {bodyData}")
        
        # Step 2: Extract filename and documentId from message
        fileName = bodyData["mssgContent"]  # Object name in MinIO
        documentId = bodyData["documentId"]  # SHA-256 hash of file
        
        # Step 3: Validate message has required data
        if not fileName:
            # Missing filename - can't process, reject message permanently
            log("ERROR: Filename missing in message")
            ch.basic_nack(delivery_tag = method.delivery_tag,requeue = False)
            return

        # Step 4: Download file from MinIO and process it
        # This function handles: download → parse → generate embeddings → store in ChromaDB
        success = downloadAndStoreFileLocallyUsingMinio(fileName,documentId)

        print("success:",success)
        
        # Step 5: Prepare acknowledgement message to send back to Spring Boot
        # Spring Boot can listen to ACKNOWLEDGEMENT_QUEUE to update DB status
        ackBody = {
            "documentId" : documentId,
            "documentName" : fileName,
            "processed" : bool(success)  # True = success, False = failed
        }
        
        # Step 6: Send ACK message back to Spring Boot (via RabbitMQ)
        # Published to exchange with ACK routing key
        # Spring Boot listener can consume this to update document status
        channel.basic_publish(
            exchange=EXCHANGE_NAME,
            routing_key=ROUTING_KEY_ACK,
            body=json.dumps(ackBody)
        )

        # Step 7: Acknowledge message to RabbitMQ based on processing result
        if success:
            log(f"File processed and ingested successfully: {fileName}")
            # Success: remove message from queue
            ch.basic_ack(delivery_tag=method.delivery_tag)
        else:
            log(f"CRITICAL: File processing failed permanently: {fileName}")
            # Failed: remove message from queue (don't retry - prevents infinite loops)
            # Could be configured to send to dead letter queue for manual inspection
            ch.basic_nack(delivery_tag=method.delivery_tag, requeue=False)
            return

    except json.JSONDecodeError as e :
        # Malformed JSON - can't process, acknowledge to prevent redelivery
        log(f"JSON decode error: {e}")
        ch.basic_ack(delivery_tag=method.delivery_tag)
        
    except Exception as e:
        # Unexpected error - log full traceback and acknowledge
        # Acknowledging prevents message from blocking queue
        # In production, might want to send to error queue instead
        log(f"Unhandled exception during message processing: {e}")
        import traceback
        traceback.print_exc()
        ch.basic_ack(delivery_tag=method.delivery_tag)


def storeText(documents,metadatas):
    """
    Stores text chunks and metadata in ChromaDB vector database.
    
    VECTOR STORAGE PROCESS:
    1. Receives parallel lists: documents (text) and metadatas (dict)
    2. Generates UUID for each document chunk (unique identifier)
    3. ChromaDB automatically:
       a. Generates embedding vector for each text chunk
       b. Stores vector + text + metadata together
       c. Builds index for fast similarity search
    
    EMBEDDING GENERATION:
    - Uses sentence-transformers model (configured in collection)
    - Converts text → 384 or 768-dimensional vector
    - Similar text → similar vectors (cosine similarity)
    - Example:
      * "What is AI?" → [0.23, -0.45, 0.67, ...]
      * "Define artificial intelligence" → [0.21, -0.43, 0.69, ...] (similar vector!)
    
    METADATA STORAGE:
    Each chunk stores metadata for filtering and display:
    - document_id: track which document this came from
    - source_heading: section context
    - filename: user-friendly reference
    - page_no: citation information
    - element_type: structural information
    - chunk_index: order for reconstruction
    - upload_date: filtering by time
    
    RETRIEVAL USAGE:
    When user asks "What is machine learning?":
    1. Question converted to embedding
    2. ChromaDB finds chunks with similar embeddings
    3. Returns top N most relevant chunks with metadata
    4. Metadata used to show source (filename, page) to user
    
    Args:
        documents: List of text chunks (strings)
        metadatas: List of metadata dicts (one per chunk)
    
    Returns:
        bool: True if stored successfully, False if no data to store
    """
    if documents and metadatas:
        log(f"Storing {len(documents)} document chunks")
        log(f"Documents: {documents}")
        log(f"Metadata: {metadatas}")
        
        # Generate unique ID for each chunk
        # UUID ensures no collisions even across distributed systems
        uuids = [str(uuid.uuid4()) for _ in documents]
        
        # Add to ChromaDB collection
        # collection.add() automatically:
        # 1. Generates embeddings using configured model
        # 2. Stores vectors in index
        # 3. Associates metadata with each vector
        collection.add(
            ids= uuids,           # Unique identifiers
            documents= documents,  # Text content (also generates embeddings)
            metadatas= metadatas   # Metadata for filtering/display
        )
        log("Text added to database successfully")
        return True
    else:
        log("No documents or metadata to store")
        return False
    

def parse(fileNameWithPath:str,filename:str,documentId:str):
    """
    Wrapper function to parse document and store results.
    Delegates to parser.parseFile() then stores in ChromaDB.
    
    FLOW:
    1. Call parser.parseFile() to extract text and metadata
    2. Receive two lists: documents and metadatas
    3. Call storeText() to save to ChromaDB vector database
    
    Args:
        fileNameWithPath: Full path to downloaded file (/tmp/xyz/file.pdf)
        filename: Original filename (file.pdf)
        documentId: SHA-256 hash of file
    """
    log(f"Parsing file: {fileNameWithPath}")
    
    # Extract text and metadata from document
    # Returns parallel lists: documents[i] corresponds to metadataToAdd[i]
    documentsToAdd,metadataToAdd = parser_ai.parseFile(fileNameWithPath,filename,documentId)
    
    # Store extracted text and metadata in ChromaDB
    storeText(documentsToAdd,metadataToAdd)
    

def downloadAndStoreFileLocallyUsingMinio(objectName : str,documentId:str):
    """
    Downloads file from MinIO and triggers parsing/storage pipeline.
    
    COMPLETE DOWNLOAD AND PROCESSING FLOW:
    1. Create temporary directory (auto-deleted when done)
    2. Construct full file path in temp directory
    3. Download file from MinIO bucket to temp path
    4. Call parse() to extract text and store in ChromaDB
    5. Temp directory automatically deleted (cleanup)
    6. Return success/failure status
    
    TEMPORARY DIRECTORY:
    - Uses Python tempfile.TemporaryDirectory context manager
    - Automatically creates unique temp directory
    - Automatically deletes directory and all files when exiting context
    - Prevents disk space leakage from processed files
    
    MINIO DOWNLOAD:
    - Downloads from BUCKET_NAME bucket
    - Object name = filename stored by Spring Boot
    - Downloads to local filesystem for processing
    - After processing, temp file is automatically deleted
    
    ERROR HANDLING:
    - Missing filename: raise exception
    - Download failure: log error and return False
    - Parsing failure: exception propagates, logged in callback
    
    Args:
        objectName: Filename/key in MinIO bucket
        documentId: SHA-256 hash for tracking
    
    Returns:
        bool: True if successful, False if error occurred
    """
    try:
        log(f"Downloading file from MinIO: {objectName}")
        
        # Create temporary directory that auto-deletes on exit
        with tempfile.TemporaryDirectory() as PATH_TO_DOWNLOAD_FILES:
            # Construct full file path: /tmp/tmpXYZ/filename.pdf
            fileNameWithPath = os.path.join(PATH_TO_DOWNLOAD_FILES, objectName)
            
            # Validate filename provided
            if not objectName:
                raise Exception("file name not provided")
            
            # Download file from MinIO using boto3 (S3-compatible client)
            # bucket_name: which bucket to download from
            # object_name: which file in the bucket
            # filename: where to save locally
            botoClient.download_file(BUCKET_NAME,objectName,fileNameWithPath)
            log(f"File downloaded successfully to: {fileNameWithPath}")
            
            # Parse document and store in ChromaDB
            parse(fileNameWithPath,objectName,documentId)
            log("Data extraction completed")
            
            # Success
            return True
        # Temp directory automatically deleted here

    except Exception as e:
        # Download or processing failed
        log(f"Download error: {e}")
        import traceback
        traceback.print_exc()
        return False

try:
    channel.basic_consume(queue=DOCUMENT_QUEUE, on_message_callback=callback)
    log("=== WORKER READY - Waiting for messages ===")
    channel.start_consuming()
except KeyboardInterrupt:
    log("Consumer stopped manually")
    connection.close()
except Exception as e:
    log(f"FATAL: Consumer crashed: {e}")
    import traceback
    traceback.print_exc()
    if 'connection' in locals() and connection.is_open:
        connection.close()




# def extractAndStoreText(fullText):
#     primaryChunks = fullText.split("\n\n")
#     finalText = []
#     # logger.info("Chunking The Received Text")
#     for chunk in primaryChunks:
#         if(len(chunk) > 1000):
#             smallChunk = chunk.split("\n")
#             for small in smallChunk:
#                 finalText.append(sanitizeText(small))
#         else:
#             finalText.append(sanitizeText(chunk))
        
#     if finalText:
#         # logger.info("Assigning Uids")
#         uuids = [str(uuid.uuid4()) for _ in finalText]
#         collection.add(
#             ids= uuids,
#             documents= finalText
#         )
#         # logger.info("Text Added To The Database Successfully")

#     # print(finalText)
#     return finalText
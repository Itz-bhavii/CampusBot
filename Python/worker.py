import os
import uuid
import boto3
import logging
import tempfile
import chromadb
import pika,os,json
import logging.config
from common import clients
from logging_config import LOGGING_CONFIG
from unstructured.partition.pdf import partition_pdf
from unstructured.partition.text import partition_text


logging.config.dictConfig(LOGGING_CONFIG)
logger = logging.getLogger(__name__)



try:
    URL = os.environ.get("CLOUDAMQP_URL")
    BUCKET_NAME = os.getenv("BUCKET_NAME")
    MINIO_ACCESS_KEY = os.getenv("MINIO_ACCESS_KEY")
    MINIO_SECRET_KEY = os.getenv("MINIO_SECRET_KEY")
    MINIO_ENDPOINT_URL = os.getenv("MINIO_ENDPOINT_URL") 

    if not URL:
        logger.critical("CLOUDAMQP_URL value not set")
        raise ValueError("CLOUDAMQP_URL not set")
    if not BUCKET_NAME:
        logger.critical("BUCKETNAME value not set")
        raise ValueError("BUCKETNAME not set")
    if not MINIO_ACCESS_KEY:
        logger.critical("MINIO_ACCESS_KEY value not set")
        raise ValueError("MINIO_ACCESS_KEY not set")
    if not MINIO_SECRET_KEY:
        logger.critical("MINIO_SECRET_KEY value not set")
        raise ValueError("MINIO_SECRET_KEY not set")
    if not MINIO_ENDPOINT_URL:
        logger.critical("MINIO_ENDPOINT_URL value not set")
        raise ValueError("MINIO_ENDPOINT_URL not set")
    
    #intellignet models for chromadb
    model = clients.getModel()
    #Chroma client
    chromaClient = chromadb.HttpClient(host="localhost",port=8000)
    # chromaClient.delete_collection("practice_collection")
    collection = chromaClient.get_or_create_collection(name="practice_collection",embedding_function=model)

    #MINIO client
    botoClient = boto3.client(
        "s3",
        endpoint_url = MINIO_ENDPOINT_URL,
        aws_access_key_id=MINIO_ACCESS_KEY,
        aws_secret_access_key=MINIO_SECRET_KEY
    )

    logger.info("Successfully initialized all clients and connected to ChromaDB And Minio.")

    #connecting to rabbitmq
    params = pika.URLParameters(URL)
    connection = pika.BlockingConnection(params)
    channel = connection.channel()
    channel.queue_declare(queue="campus-bot-q",durable=True)

except Exception as e:
    logger.error("failed to connect to RabbitMQ",exc_info=True)
    exit(1)


def callback(ch,method,properties,body):

    log_context = {
        'delivery_tag': method.delivery_tag,
        'app_id': properties.app_id if properties else 'N/A'
    }

    try:
        jsonString = body.decode()
        bodyData = json.loads(jsonString)
        print("received:",bodyData)
        logger.info("File Name Received Successfully")
        fileName = bodyData["mssgContent"]
        
        if not fileName:
            logger.error("file path is missing")
            ch.basic_nack(delivery_tag = method.delivery_tag,requeue = False)

        log_context["filePath"] = fileName
        logger.info("Received message to process file",extra=log_context)

        downloadAndStoreFileLocallyUsingMinio(fileName)
        logger.info("successfully received and ingested file",extra=log_context)

        ch.basic_ack(delivery_tag=method.delivery_tag)

    except json.JSONDecodeError as e :
        logger.error(f"failed to decode json from message body.",extra=log_context)
        print("Check the format properly")
        ch.basic_ack(delivery_tag=method.delivery_tag)
    except Exception as e:
        logger.error("unhandled exception occurred during message processing ",e,extra=log_context)
        ch.basic_ack(delivery_tag=method.delivery_tag)

def cleanText(text):
    cleanedText = ' '.join(str(text).split())
    return cleanedText

def extractAndStoreText(fullText):
    primaryChunks = fullText.split("\n\n")
    finalText = []
    logger.info("Chunking The Received Text")
    for chunk in primaryChunks:
        if(len(chunk) > 1000):
            smallChunk = chunk.split("\n")
            for small in smallChunk:
                finalText.append(cleanText(small))
        else:
            finalText.append(cleanText(chunk))
        
    if finalText:
        logger.info("Assigning Uids")
        uuids = [str(uuid.uuid4()) for _ in finalText]
        collection.add(
            ids= uuids,
            documents= finalText
        )
        logger.info("Text Added To The Database Successfully")

    # print(finalText)
    return finalText


def getFileDataAndExtract(fileNameWithPath:str):
    if(".pdf" in fileNameWithPath):
        doc = partition_pdf(fileNameWithPath,strategy="hi_res")
        logger.info("Opened The Pdf File")
    elif(".txt" in fileNameWithPath):
        doc = partition_text(fileNameWithPath)
        logger.info("Opened The Text File")
    else:
        logger.error("Invalid File Format")
        raise Exception("Invalid File Format")
    fullText = ""
    for page in doc:
        fullText += page.text + "\n"

    # print(fullText)

    extractAndStoreText(fullText)

    textToReturn = {
        "content" : "Text Extracted Successfully"
    }

    return textToReturn

def downloadAndStoreFileLocallyUsingMinio(objectName : str):
    try:
        with tempfile.TemporaryDirectory() as PATH_TO_DOWNLOAD_FILES:
            fileNameWithPath = os.path.join(PATH_TO_DOWNLOAD_FILES, objectName)
            if not objectName:
                raise Exception("file name not provided")
            botoClient.download_file(BUCKET_NAME,objectName,fileNameWithPath)
            logger.info("file downloaded successfully at",fileNameWithPath)
            getFileDataAndExtract(fileNameWithPath)
            logger.info("data extraction successfull")

    except Exception as e:
        logger.error(f"download error {e}")
        return ""

try:
    channel.basic_consume(queue="campus-bot-q", on_message_callback=callback)
    logger.info("Starting to consume messages. Waiting for jobs...")
    channel.start_consuming()
except KeyboardInterrupt:
    logger.info("Consumer stopped manually.")
    connection.close()
except Exception as e:
    logger.critical("Consumer crashed.", exc_info=True)
    if 'connection' in locals() and connection.is_open:
        connection.close()
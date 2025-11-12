import os
import re
import uuid
import boto3
import tabula
# import logging
print("before parser")
from . import parser
print("after parser")
import tempfile
import chromadb
import pika,json
import pandas as pd
# import logging.config
from campusbot.common import clients
from collections import defaultdict
# from campusbot.common.campus_logger import LOGGING_CONFIG
from unstructured.partition.pdf import partition_pdf
from unstructured.partition.text import partition_text
from langchain_text_splitters import RecursiveCharacterTextSplitter
from unstructured.documents.elements import Title,NarrativeText,ListItem,Table
print("imports successfull")

# logging.config.dictConfig(LOGGING_CONFIG)
# logger = logging.getLogger(__name__)

print("logger success")


try:
    URL = os.environ.get("CLOUDAMQP_URL")
    BUCKET_NAME = os.getenv("BUCKET_NAME")
    MINIO_ACCESS_KEY = os.getenv("MINIO_ACCESS_KEY")
    MINIO_SECRET_KEY = os.getenv("MINIO_SECRET_KEY")
    MINIO_ENDPOINT_URL = os.getenv("MINIO_ENDPOINT_URL") 
    print("got env vars")

    if not URL:
        # logger.critical("CLOUDAMQP_URL value not set")
        raise ValueError("CLOUDAMQP_URL not set")
    if not BUCKET_NAME:
        # logger.critical("BUCKETNAME value not set")
        raise ValueError("BUCKETNAME not set")
    if not MINIO_ACCESS_KEY:
        # logger.critical("MINIO_ACCESS_KEY value not set")
        raise ValueError("MINIO_ACCESS_KEY not set")
    if not MINIO_SECRET_KEY:
        # logger.critical("MINIO_SECRET_KEY value not set")
        raise ValueError("MINIO_SECRET_KEY not set")
    if not MINIO_ENDPOINT_URL:
        # logger.critical("MINIO_ENDPOINT_URL value not set")
        raise ValueError("MINIO_ENDPOINT_URL not set")
    
    #intellignet models for chromadb
    model = clients.getModel()
    #Chroma client
    chromaClient = chromadb.HttpClient(host="chromadb",port=8000)
    # chromaClient.delete_collection("practice_collection")
    collection = chromaClient.get_or_create_collection(name="practice_collection",embedding_function=model)
    print("chroma done")
    #MINIO client
    botoClient = boto3.client(
        "s3",
        endpoint_url = MINIO_ENDPOINT_URL,
        aws_access_key_id=MINIO_ACCESS_KEY,
        aws_secret_access_key=MINIO_SECRET_KEY
    )

    # logger.info("Successfully initialized all clients and connected to ChromaDB And Minio.")

    print("minio done")
    # RabbitMQ constants
    QUEUE_NAME = "campus-bot-q"
    EXCHANGE_NAME = "main-exchange"
    ROUTING_KEY = "campus.bot.events"

    #connecting to rabbitmq
    params = pika.URLParameters(URL)
    connection = pika.BlockingConnection(params)
    channel = connection.channel()

    # Declare the topic exchange
    channel.exchange_declare(exchange=EXCHANGE_NAME, exchange_type='topic', durable=True)

    print("rabbit done")
    # Declare the durable queue
    channel.queue_declare(queue=QUEUE_NAME, durable=True)

    # Bind the queue to the exchange with the routing key
    channel.queue_bind(queue=QUEUE_NAME, exchange=EXCHANGE_NAME, routing_key=ROUTING_KEY)
    print("connected to queue")

except Exception as e:
    print("cannot connect")
    # logger.error("failed to connect to RabbitMQ",exc_info=True)
    exit(1)


def callback(ch,method,properties,body):

    # log_context = {
    #     'delivery_tag': method.delivery_tag,
    #     'app_id': properties.app_id if properties else 'N/A'
    # }
    print("callback called")

    try:
        jsonString = body.decode()
        bodyData = json.loads(jsonString)
        print("received:",bodyData)
        # logger.info("File Name Received Successfully")
        fileName = bodyData["mssgContent"]
        
        if not fileName:
            # logger.error("file path is missing")
            ch.basic_nack(delivery_tag = method.delivery_tag,requeue = False)

        # log_context["filePath"] = fileName
        # logger.info("Received message to process file",extra=log_context)

        downloadAndStoreFileLocallyUsingMinio(fileName)
        # logger.info("successfully received and ingested file",extra=log_context)

        ch.basic_ack(delivery_tag=method.delivery_tag)

    except json.JSONDecodeError as e :
        # logger.error(f"failed to decode json from message body.",extra=log_context)
        print("Check the format properly")
        ch.basic_ack(delivery_tag=method.delivery_tag)
    except Exception as e:
        # logger.error("unhandled exception occurred during message processing ",e,extra=log_context)
        ch.basic_ack(delivery_tag=method.delivery_tag)

def sanitizeText(text: str) -> str:
    # 1. Fix words broken across lines
    text = re.sub(r'-\n', '', text)
    # 2. Remove page numbers, headers, footers (customize this regex)
    text = re.sub(r'\d+ of \d+', '', text)
    # 3. Collapse all whitespace into single spaces
    text = re.sub(r'\s+', ' ', text).strip()
    return text


def storeText(documents,metadatas):
    grouped_chunks = defaultdict(list)

    for i in range(len(documents)):
        heading = metadatas[i]["source_heading"]
        chunk = documents[i]
        grouped_chunks[heading].append(chunk)

    # 2. COMBINE the chunks for each heading into a single paragraph.
    # This is the critical step your original code failed at.
    final_data = {
        heading: " ".join(chunks)
        for heading, chunks in grouped_chunks.items()
    }

    # 3. UNPACK the final, aggregated data into lists for the database.
    final_documents = list(final_data.values())
    final_metadatas = [{"source_heading": heading} for heading in final_data.keys()]

    if documents:
        print(final_documents)
        print(final_metadatas)
        # logger.info("Assigning Uids")
        uuids = [str(uuid.uuid4()) for _ in final_documents]
        collection.add(
            ids= uuids,
            documents= final_documents,
            metadatas=final_metadatas
        )
        # logger.info("Text Added To The Database Successfully")

    # print(finalText)



def parse(fileNameWithPath:str):
    # documentsToAdd,metadataToAdd = parser.parseFile(fileNameWithPath)   
    # storeText(documentsToAdd,metadataToAdd)
    print(fileNameWithPath)
    # textToReturn = {
    #     "content" : "Text Extracted Successfully"
    # }

    # return textToReturn

def downloadAndStoreFileLocallyUsingMinio(objectName : str):
    try:
        with tempfile.TemporaryDirectory() as PATH_TO_DOWNLOAD_FILES:
            fileNameWithPath = os.path.join(PATH_TO_DOWNLOAD_FILES, objectName)
            if not objectName:
                raise Exception("file name not provided")
            botoClient.download_file(BUCKET_NAME,objectName,fileNameWithPath)
            # logger.info("file downloaded successfully at",fileNameWithPath)
            print("downloaded")
            parse(fileNameWithPath)
            # logger.info("data extraction successfull")

    except Exception as e:
        # logger.error(f"download error {e}")
        return ""

try:
    channel.basic_consume(queue="campus-bot-q", on_message_callback=callback)
    # logger.info("Starting to consume messages. Waiting for jobs...")
    print("started consuming")
    channel.start_consuming()
except KeyboardInterrupt:
    # logger.info("Consumer stopped manually.")
    connection.close()
except Exception as e:
    # logger.critical("Consumer crashed.", exc_info=True)
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
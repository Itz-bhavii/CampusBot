import pika,os,json
import logging
import logging.config
from ingest_server import getFileDataAndExtract
from logging_config import LOGGING_CONFIG

logging.config.dictConfig(LOGGING_CONFIG)
logger = logging.getLogger(__name__)

try:
    url = os.environ.get("CLOUDAMQP_URL")
    if not url:
        logger.critical("CLOUDAMQP_URL value not set")
        raise ValueError("CLOUDAMQP_URL not set")
    params = pika.URLParameters(url)
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
        logger.info("File Received Successfully")
        fileNameWithPath = bodyData["mssgContent"]
        
        if not fileNameWithPath:
            logger.error("file path is missing")
            ch.basic_nack(delivery_tag = method.delivery_tag,requeue = False)

        log_context["filePath"] = fileNameWithPath
        logger.info("Received message to process file",extra=log_context)
        print(getFileDataAndExtract(fileNameWithPath))
        logger.info("successfully received and ingested file",extra=log_context)
        ch.basic_ack(delivery_tag=method.delivery_tag)

    except json.JSONDecodeError as e :
        logger.error(f"failed to decode json from message body.",extra=log_context)
        print("Check the format properly")
        ch.basic_ack(delivery_tag=method.delivery_tag)
    except Exception as e:
        logger.error("unhandled exception occurred during message processing",extra=log_context)
        ch.basic_ack(delivery_tag=method.delivery_tag)



        

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
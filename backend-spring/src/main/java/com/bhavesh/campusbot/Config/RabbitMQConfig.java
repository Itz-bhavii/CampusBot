package com.bhavesh.campusbot.Config;

import org.springframework.amqp.core.Binding;
import org.springframework.amqp.core.BindingBuilder;
import org.springframework.amqp.core.Queue;
import org.springframework.amqp.core.TopicExchange;
import org.springframework.amqp.support.converter.Jackson2JsonMessageConverter;
import org.springframework.amqp.support.converter.MessageConverter;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;

/**
 * RabbitMQ configuration for asynchronous messaging between Spring Boot and Python workers.
 * Sets up queues, exchanges, and bindings for document processing workflow.
 * 
 * RABBITMQ ARCHITECTURE:
 * Publisher (Spring Boot) → Exchange → Queue → Consumer (Python Worker)
 * 
 * MESSAGING FLOW:
 * 1. Document Upload Flow:
 *    Spring Boot → EXCHANGE_NAME → ROUTING_KEY_DOC → DOCUMENT_QUEUE → Python Ingestion Worker
 * 
 * 2. Acknowledgement Flow (future use):
 *    Python Worker → EXCHANGE_NAME → ROUTING_KEY_ACK → ACKNOWLEDGEMENT_QUEUE → Spring Boot Listener
 * 
 * WHY RABBITMQ:
 * - Decouples Spring Boot from Python workers (async processing)
 * - Python workers can be scaled independently
 * - If worker crashes, messages remain in queue (reliability)
 * - Spring Boot doesn't wait for slow document processing
 * 
 * TOPIC EXCHANGE PATTERN:
 * Uses routing keys for flexible message routing:
 * - "campusbot.documents" routes to document queue
 * - "campusbot.acknowledgements" routes to ack queue
 * - Can add more queues with different routing keys later
 */
@Configuration
public class RabbitMQConfig {
    
    // Queue name where document processing messages are sent
    // Python ingestion worker listens to this queue
    public static final String DOCUMENT_QUEUE = "documents.queue";
    
    // Queue name for acknowledgements from Python workers (future use)
    public static final String ACKNOWLEDGEMENT_QUEUE = "acknowledgements.queue";
    
    // Topic exchange name - routes messages based on routing keys
    public static final String EXCHANGE_NAME = "main-exchange";
    
    // Routing key for document messages
    // Messages sent with this key go to DOCUMENT_QUEUE
    public static final String ROUTING_KEY_DOC = "campusbot.documents";
    
    // Routing key for acknowledgement messages
    public static final String ROUTING_KEY_ACK = "campusbot.acknowledgements";

    /**
     * Creates the queue for document processing messages.
     * 
     * QUEUE PROPERTIES:
     * - Name: "documents.queue"
     * - Durable: true (survives RabbitMQ server restart)
     * 
     * DURABILITY IMPORTANCE:
     * If RabbitMQ restarts, durable queues and their messages persist.
     * Without durability, messages would be lost during restart.
     * 
     * CONSUMER:
     * Python ingestion worker connects to this queue and waits for messages.
     * Each message contains documentId and filename in MinIO.
     * 
     * @return Queue bean for document processing
     */
    @Bean
    public Queue documentQueue(){
        return new Queue(DOCUMENT_QUEUE,true);  // true = durable
    }

    /**
     * Creates the queue for acknowledgement messages (currently for future use).
     * Python workers can send acknowledgements back to Spring Boot.
     * 
     * POTENTIAL USE:
     * - Worker completes processing → sends ack → Spring Boot updates DB status
     * - Worker fails → sends error → Spring Boot retries or alerts admin
     * 
     * @return Queue bean for acknowledgements
     */
    @Bean
    public Queue acknowledgementQueue(){
        return new Queue(ACKNOWLEDGEMENT_QUEUE,true);  // true = durable
    }
    
    /**
     * Creates topic exchange for routing messages.
     * 
     * TOPIC EXCHANGE:
     * Routes messages to queues based on routing key patterns.
     * - Exact match: "campusbot.documents" only goes to document queue
     * - Wildcards supported: "campusbot.*" would match all campusbot routing keys
     * 
     * This is more flexible than direct exchange (exact match only)
     * or fanout exchange (broadcasts to all queues).
     * 
     * @return TopicExchange bean
     */
    @Bean
    public TopicExchange exchange(){
        return new TopicExchange(EXCHANGE_NAME);
    }
    
    /**
     * Binds document queue to exchange with document routing key.
     * 
     * BINDING LOGIC:
     * When message is sent to EXCHANGE_NAME with routing key ROUTING_KEY_DOC,
     * RabbitMQ routes it to DOCUMENT_QUEUE.
     * 
     * FLOW:
     * rabbitTemplate.convertAndSend(EXCHANGE_NAME, ROUTING_KEY_DOC, message)
     * → Exchange receives message
     * → Checks routing key = "campusbot.documents"
     * → Finds binding: "campusbot.documents" → DOCUMENT_QUEUE
     * → Delivers message to DOCUMENT_QUEUE
     * → Python worker consumes from DOCUMENT_QUEUE
     * 
     * @param documentQueue The queue to bind
     * @param topicExchange The exchange to bind to
     * @return Binding configuration
     */
    @Bean
    public Binding documentBinding(Queue documentQueue,TopicExchange topicExchange){
        return BindingBuilder.bind(documentQueue).to(topicExchange).with(ROUTING_KEY_DOC);
    }
    
    /**
     * Binds acknowledgement queue to exchange with ack routing key.
     * Python workers can send messages with ROUTING_KEY_ACK to reach this queue.
     * 
     * @param acknowledgementQueue The queue to bind
     * @param topicExchange The exchange to bind to
     * @return Binding configuration
     */
    @Bean
    public Binding acknowledgementBinding(Queue acknowledgementQueue,TopicExchange topicExchange){
        return BindingBuilder.bind(acknowledgementQueue).to(topicExchange).with(ROUTING_KEY_ACK);
    }

    /**
     * Configures JSON message converter for RabbitMQ.
     * 
     * MESSAGE SERIALIZATION:
     * Without converter: messages are sent as raw bytes
     * With JSON converter: Java objects automatically serialized to JSON
     * 
     * EXAMPLE:
     * Java: new CustomMessage("abc123", "document.pdf")
     * RabbitMQ: {"documentId":"abc123","mssgContent":"document.pdf"}
     * Python: receives JSON, deserializes to dict
     * 
     * This allows seamless communication between Java and Python
     * using JSON as the common format.
     * 
     * Jackson library is used for JSON serialization/deserialization.
     * 
     * @return Jackson-based message converter
     */
    @Bean
    public MessageConverter jsonMessageConverter(){
        return new Jackson2JsonMessageConverter();
    }
}

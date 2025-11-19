package com.bhavesh.campusbot.Config;

import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;
import org.springframework.web.client.RestTemplate;

/**
 * Master configuration class for general application-wide beans.
 * Contains bean definitions that don't fit into more specific config classes.
 */
@Configuration
public class MasterConfig {
    
    /**
     * Creates RestTemplate bean for making HTTP requests to external services.
     * 
     * USAGE IN APPLICATION:
     * - QueryService uses this to call Python AI service
     * - IngestionService uses this for legacy image processing endpoint
     * 
     * RestTemplate is Spring's synchronous HTTP client:
     * - Supports GET, POST, PUT, DELETE requests
     * - Automatically serializes/deserializes JSON using Jackson
     * - Thread-safe - single instance can be shared across services
     * 
     * @return RestTemplate instance for dependency injection
     */
    @Bean
    public RestTemplate restTemplate(){
        return new RestTemplate();
    }
}

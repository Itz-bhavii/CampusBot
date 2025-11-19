package com.bhavesh.campusbot.Services;

import org.springframework.boot.CommandLineRunner;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Profile;
import org.springframework.security.crypto.password.PasswordEncoder;
import org.springframework.stereotype.Component;

import com.bhavesh.campusbot.Entities.Users;
import com.bhavesh.campusbot.Repositorys.UserDetailsRepository;

/**
 * Initializes a default admin user when the application starts.
 * This ensures there's always at least one admin account available for initial setup.
 * 
 * STARTUP FLOW:
 * 1. Application starts up
 * 2. Spring Boot runs all CommandLineRunner beans after context is loaded
 * 3. This bean checks if admin user already exists
 * 4. If not exists: creates admin user with default credentials
 * 5. Application continues normal startup
 * 
 * SECURITY NOTE:
 * Default credentials are: username="admin", password="admin1234"
 * These should be changed immediately in production!
 * 
 * @Profile("!test") means this only runs in non-test environments
 * (prevents creating admin during unit/integration tests)
 */
@Component
@Profile("!test")  // Excluded from test profile to avoid interference with test data
public class DefaultAdminInitializer {
    
    /**
     * Creates a CommandLineRunner that executes during application startup.
     * CommandLineRunner is a Spring Boot interface that runs code after the application context is loaded.
     * 
     * EXECUTION FLOW:
     * 1. Spring Boot completes initialization of all beans
     * 2. Runs this CommandLineRunner
     * 3. Checks database for existing admin user
     * 4. If no admin exists:
     *    a. Creates new Users entity
     *    b. Sets username to "admin"
     *    c. Hashes password "admin1234" using BCrypt
     *    d. Assigns ADMIN role for full system access
     *    e. Saves to database
     * 5. Application becomes ready to accept requests
     * 
     * @param userDetailsRepository Repository to check/save admin user
     * @param passwordEncoder BCrypt encoder to hash the password before storing
     * @return Lambda function that will be executed at startup
     */
    @Bean
    public CommandLineRunner commandLineRunner(UserDetailsRepository userDetailsRepository,PasswordEncoder passwordEncoder){
        return args->{
            // Check if admin user already exists in database
            if(userDetailsRepository.findByUsername("admin").isEmpty()){
                // Admin doesn't exist - create it
                Users admin = new Users();
                admin.setUsername("admin");
                // Hash the password using BCrypt before storing (never store plain text passwords!)
                admin.setPassword(passwordEncoder.encode("admin1234"));
                // Assign ADMIN role for full privileges
                admin.setRole("ADMIN");
                // Persist to database
                userDetailsRepository.save(admin);
                System.out.println("Default Admin Created With admin admin1234");
            }
        };
    }
}

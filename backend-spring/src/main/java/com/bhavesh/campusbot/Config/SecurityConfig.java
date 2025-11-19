package com.bhavesh.campusbot.Config;

import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;
import org.springframework.http.HttpMethod;
import org.springframework.security.authentication.AuthenticationManager;
import org.springframework.security.authentication.ProviderManager;
import org.springframework.security.authentication.dao.DaoAuthenticationProvider;
import org.springframework.security.config.Customizer;
import org.springframework.security.config.annotation.web.builders.HttpSecurity;
import org.springframework.security.config.annotation.web.configuration.EnableWebSecurity;
import org.springframework.security.config.http.SessionCreationPolicy;
import org.springframework.security.crypto.bcrypt.BCryptPasswordEncoder;
import org.springframework.security.crypto.password.PasswordEncoder;
import org.springframework.security.web.SecurityFilterChain;
import org.springframework.security.web.authentication.UsernamePasswordAuthenticationFilter;
import org.springframework.web.cors.CorsConfiguration;
import org.springframework.web.cors.CorsConfigurationSource;
import org.springframework.web.cors.UrlBasedCorsConfigurationSource;

import com.bhavesh.campusbot.Filters.JwtAuthFilter;
import com.bhavesh.campusbot.Services.CustomUserDetailsService;

import java.util.Arrays;

import org.springframework.beans.factory.annotation.Autowired;

/**
 * Security configuration for the CampusBot application.
 * Implements JWT-based stateless authentication with Spring Security.
 * 
 * SECURITY ARCHITECTURE:
 * 1. User sends login credentials → AuthenticationManager validates
 * 2. If valid: JWT token generated and returned to user
 * 3. User stores JWT in browser (localStorage/sessionStorage)
 * 4. Every subsequent request: user sends JWT in Authorization header
 * 5. JwtAuthFilter intercepts request, validates JWT, authenticates user
 * 6. If valid: request proceeds to controller
 * 7. If invalid: returns 401 Unauthorized
 * 
 * STATELESS SESSIONS:
 * No server-side session storage (no JSESSIONID cookies)
 * All authentication state is in the JWT itself
 * Enables horizontal scaling (any server can handle any request)
 * 
 * KEY COMPONENTS:
 * - SecurityFilterChain: defines which URLs require authentication
 * - AuthenticationManager: validates username/password during login
 * - JwtAuthFilter: validates JWT tokens on every request
 * - PasswordEncoder: hashes passwords using BCrypt
 */
@Configuration
@EnableWebSecurity  // Enables Spring Security for the application
public class SecurityConfig{

    // Custom JWT filter that validates tokens on each request
    @Autowired
    JwtAuthFilter jwtAuthFilter;

    /**
     * Configures the security filter chain - defines security rules for HTTP requests.
     * 
     * SECURITY FLOW:
     * Request arrives → CORS check → CSRF check → Authorization check → JWT validation → Controller
     * 
     * CONFIGURATION BREAKDOWN:
     * 
     * 1. CSRF DISABLED:
     *    - CSRF protection not needed for stateless JWT authentication
     *    - CSRF protects against session-based attacks
     *    - Since we don't use sessions, it's unnecessary
     * 
     * 2. CORS ENABLED:
     *    - Allows frontend (localhost:3000) to call backend APIs
     *    - Without CORS, browser blocks cross-origin requests
     * 
     * 3. AUTHORIZATION RULES:
     *    PUBLIC ENDPOINTS (no authentication required):
     *    - /api/authenticate/** → login, register endpoints
     *    - GET /api/courses/** → anyone can view courses
     *    - /h2-console/** → H2 database console (development only)
     *    - OPTIONS /api/** → preflight requests for CORS
     *    
     *    PROTECTED ENDPOINTS (authentication required):
     *    - ALL other requests → must have valid JWT
     * 
     * 4. STATELESS SESSION:
     *    - SessionCreationPolicy.STATELESS → no server-side sessions
     *    - Each request must contain JWT for authentication
     *    - Server doesn't remember previous requests
     * 
     * 5. JWT FILTER:
     *    - JwtAuthFilter added BEFORE UsernamePasswordAuthenticationFilter
     *    - Intercepts requests, validates JWT, sets authentication in SecurityContext
     *    - If JWT valid: request proceeds
     *    - If JWT invalid/missing: request blocked (401 for protected endpoints)
     * 
     * @param http HttpSecurity builder for configuring security
     * @return SecurityFilterChain with configured security rules
     * @throws Exception if configuration fails
     */
    @Bean
    public SecurityFilterChain filterChain(HttpSecurity http) throws Exception{
        http.csrf(csrf->csrf.disable())  // Disable CSRF for stateless JWT auth
        .cors(Customizer.withDefaults())  // Enable CORS with custom config below
        .authorizeHttpRequests(auth-> auth
            .requestMatchers("/api/authenticate/**").permitAll()  // Login/register - public
            .requestMatchers(HttpMethod.GET,"/api/courses/**","/h2-console/**").permitAll()  // Read courses - public
            .requestMatchers(HttpMethod.OPTIONS, "/api/**").permitAll()  // CORS preflight - public
            .anyRequest().authenticated())  // Everything else requires authentication

        .sessionManagement(session -> session.sessionCreationPolicy(SessionCreationPolicy.STATELESS));  // No sessions
        
        // Add JWT filter before standard username/password filter
        // This ensures JWT is validated before standard authentication
        http.addFilterBefore(jwtAuthFilter, UsernamePasswordAuthenticationFilter.class);
        
        return http.build();
    }


    /**
     * Configures CORS (Cross-Origin Resource Sharing) to allow frontend access.
     * 
     * CORS PROBLEM:
     * Frontend runs on http://localhost:3000
     * Backend runs on http://localhost:8080
     * Browser blocks requests from 3000 to 8080 (different origins)
     * 
     * CORS SOLUTION:
     * Backend tells browser "I allow requests from localhost:3000"
     * Browser then permits the cross-origin requests
     * 
     * CONFIGURATION:
     * - Allowed Origins: http://localhost:3000 (Next.js frontend)
     * - Allowed Methods: GET, POST, PUT, DELETE, OPTIONS
     * - Allowed Headers: * (all headers)
     * - Allow Credentials: true (allows cookies and Authorization header)
     * 
     * PREFLIGHT REQUESTS:
     * For POST/PUT/DELETE, browser sends OPTIONS request first (preflight)
     * Server responds with allowed methods/headers
     * Browser then sends actual request
     * 
     * @return CorsConfigurationSource with frontend access permissions
     */
    @Bean
    CorsConfigurationSource corsConfigurationSource() {
        CorsConfiguration configuration = new CorsConfiguration();
        
        // Allow frontend origin
        configuration.setAllowedOrigins(Arrays.asList("http://localhost:3000"));
        
        // Allow common HTTP methods
        configuration.setAllowedMethods(Arrays.asList("GET", "POST", "PUT", "DELETE", "OPTIONS"));
        
        // Allow all headers (includes Authorization header for JWT)
        configuration.setAllowedHeaders(Arrays.asList("*"));
        
        // Allow credentials (required for Authorization header)
        configuration.setAllowCredentials(true);

        UrlBasedCorsConfigurationSource source = new UrlBasedCorsConfigurationSource();
        
        // Apply this CORS config to all API endpoints
        source.registerCorsConfiguration("/api/**", configuration);
        
        return source;
    }

    /**
     * Creates BCrypt password encoder for hashing passwords.
     * 
     * PASSWORD SECURITY:
     * - NEVER store passwords in plain text
     * - BCrypt hashes password with salt (random data)
     * - Same password → different hash each time (due to random salt)
     * - Computationally expensive → slows down brute force attacks
     * 
     * HASHING PROCESS:
     * User registers with password "mypassword123"
     * BCrypt hashes → "$2a$10$N9qo8uLOickgx2ZMRZoMyeIjZAgcfl7p92ldGxad68LJZdL17lhWy"
     * Stored in database → only hash, never plain password
     * 
     * LOGIN VERIFICATION:
     * User logs in with "mypassword123"
     * BCrypt hashes input and compares with stored hash
     * If match: authentication successful
     * If no match: authentication failed
     * 
     * BCrypt automatically handles:
     * - Salt generation
     * - Work factor (computational cost)
     * - Secure comparison
     * 
     * @return BCryptPasswordEncoder for password hashing
     */
    @Bean
    public PasswordEncoder passwordEncoder(){
        return new BCryptPasswordEncoder();
    }

    /**
     * Creates AuthenticationManager for validating login credentials.
     * 
     * AUTHENTICATION FLOW:
     * 1. User submits username + password to /api/authenticate/login
     * 2. AuthenticationController calls authenticationManager.authenticate()
     * 3. AuthenticationManager delegates to DaoAuthenticationProvider
     * 4. DaoAuthenticationProvider:
     *    a. Calls CustomUserDetailsService.loadUserByUsername(username)
     *    b. Gets User entity from database (contains hashed password)
     *    c. Uses PasswordEncoder.matches() to compare passwords
     *    d. If match: creates authenticated Authentication object
     *    e. If no match: throws BadCredentialsException
     * 5. If authenticated: controller generates JWT
     * 6. If not authenticated: returns 401 error
     * 
     * COMPONENTS:
     * - DaoAuthenticationProvider: handles database-based authentication
     * - UserDetailsService: loads user from database
     * - PasswordEncoder: verifies password hash
     * - ProviderManager: manages authentication providers (can have multiple)
     * 
     * WHY SEPARATE PROVIDER:
     * Allows multiple authentication methods (database, LDAP, OAuth, etc.)
     * Currently using only DaoAuthenticationProvider (database authentication)
     * 
     * @param userDetailsService Custom service to load users from database
     * @param passwordEncoder BCrypt encoder to verify passwords
     * @return AuthenticationManager for login validation
     */
    @Bean
    public AuthenticationManager authenticationManager(CustomUserDetailsService userDetailsService,PasswordEncoder passwordEncoder){
        // Create provider for database authentication
        DaoAuthenticationProvider daoAuthenticationProvider = new DaoAuthenticationProvider();
        
        // Set service to load user details from database
        daoAuthenticationProvider.setUserDetailsService(userDetailsService);
        
        // Set encoder to verify password hashes
        daoAuthenticationProvider.setPasswordEncoder(passwordEncoder);

        // Return manager with configured provider
        return new ProviderManager(daoAuthenticationProvider);
    }
}

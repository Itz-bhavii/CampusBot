package com.bhavesh.campusbot.Filters;

import java.io.IOException;

import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.security.authentication.UsernamePasswordAuthenticationToken;
import org.springframework.security.core.context.SecurityContextHolder;
import org.springframework.security.core.userdetails.UserDetails;
import org.springframework.stereotype.Component;
import org.springframework.web.filter.OncePerRequestFilter;

import com.bhavesh.campusbot.Services.CustomUserDetailsService;
import com.bhavesh.campusbot.Utils.JwtUtils;

import jakarta.servlet.FilterChain;
import jakarta.servlet.ServletException;
import jakarta.servlet.http.HttpServletRequest;
import jakarta.servlet.http.HttpServletResponse;

/**
 * JWT Authentication Filter - validates JWT tokens on EVERY incoming request.
 * This is the gatekeeper that protects all endpoints requiring authentication.
 * 
 * FILTER CHAIN POSITION:
 * Request → JwtAuthFilter (this class) → UsernamePasswordAuthenticationFilter → Controllers
 * 
 * COMPLETE AUTHENTICATION FLOW (from login to authenticated request):
 * 
 * STEP 1 - LOGIN (happens once):
 * User sends POST /api/authenticate/login with {username, password}
 * → AuthenticationManager validates credentials
 * → If valid: JWT generated and returned to user
 * → User stores JWT in browser (localStorage/sessionStorage)
 * 
 * STEP 2 - AUTHENTICATED REQUESTS (every subsequent request):
 * User sends GET /api/chat with header: "Authorization: Bearer <JWT_TOKEN>"
 * → THIS FILTER intercepts the request
 * → Extracts and validates JWT
 * → If valid: sets authentication in SecurityContext
 * → Request proceeds to ChatController
 * → Controller can access authenticated user via SecurityContextHolder
 * 
 * WHY THIS FILTER:
 * - Spring Security needs to know WHO is making the request
 * - JWT contains the username in encrypted form
 * - This filter decrypts JWT and tells Spring Security who the user is
 * - Controllers can then check user permissions and access user data
 * 
 * OncePerRequestFilter ensures this runs exactly once per request
 * (even if request is forwarded internally)
 */
@Component
public class JwtAuthFilter extends OncePerRequestFilter{

    // Utility class for JWT operations (generate, validate, extract claims)
    @Autowired
    private JwtUtils jwtUtils;

    // Service to load user details from database
    @Autowired
    private CustomUserDetailsService customUserDetailsService;

    /**
     * Main filter method - executes for EVERY HTTP request.
     * 
     * COMPLETE FLOW BREAKDOWN:
     * 
     * 1. EXTRACT JWT FROM REQUEST:
     *    - Looks for "Authorization" header
     *    - Expected format: "Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
     *    - "Bearer " is a prefix, actual token starts after space
     *    - If header missing or wrong format: token = null
     * 
     * 2. EXTRACT USERNAME FROM JWT:
     *    - JWT is in 3 parts: header.payload.signature
     *    - Payload contains claims including "subject" (username)
     *    - JwtUtils decodes payload and extracts username
     *    - If token invalid/malformed: username = null
     * 
     * 3. CHECK IF AUTHENTICATION NEEDED:
     *    - If username == null: no valid JWT, skip authentication
     *      (request might be for public endpoint like /login)
     *    - If SecurityContext already has authentication: skip
     *      (prevents re-authenticating same request)
     * 
     * 4. LOAD USER FROM DATABASE:
     *    - Uses username from JWT to query database
     *    - CustomUserDetailsService.loadUserByUsername(username)
     *    - Returns User entity with username, password hash, roles
     *    - This ensures user still exists and hasn't been deleted
     * 
     * 5. VALIDATE JWT TOKEN:
     *    - Checks if username in JWT matches username from database
     *    - Checks if token hasn't expired
     *    - Verifies signature to ensure token wasn't tampered with
     *    - If any check fails: authentication rejected
     * 
     * 6. SET AUTHENTICATION IN SECURITY CONTEXT:
     *    - Creates UsernamePasswordAuthenticationToken with:
     *      * principal: UserDetails (the user)
     *      * credentials: null (password not needed after authentication)
     *      * authorities: user roles (ADMIN, USER, etc.)
     *    - Stores in SecurityContextHolder
     *    - Spring Security now knows WHO is making this request
     *    - Controllers can access user via:
     *      SecurityContextHolder.getContext().getAuthentication().getName()
     * 
     * 7. CONTINUE FILTER CHAIN:
     *    - Whether authentication succeeded or not, request continues
     *    - If endpoint requires authentication and user not authenticated:
     *      Spring Security will return 401 Unauthorized
     *    - If endpoint is public or user is authenticated: request proceeds
     * 
     * EXAMPLE SCENARIOS:
     * 
     * Scenario A - Valid JWT:
     * Header: "Authorization: Bearer valid_token_here"
     * → Extract "valid_token_here"
     * → Extract username "john" from token
     * → Load john's details from database
     * → Validate token: ✓ signature valid, ✓ not expired
     * → Set authentication with john's details
     * → Request proceeds as authenticated user "john"
     * 
     * Scenario B - Expired JWT:
     * Header: "Authorization: Bearer expired_token"
     * → Extract username from token
     * → Load user from database
     * → Validate token: ✓ signature valid, ✗ token expired
     * → Authentication NOT set
     * → If endpoint protected: returns 401
     * 
     * Scenario C - No JWT:
     * Header: (no Authorization header)
     * → token = null, username = null
     * → Skip authentication
     * → If endpoint public (/login): request proceeds
     * → If endpoint protected: returns 401
     * 
     * Scenario D - Tampered JWT:
     * Header: "Authorization: Bearer tampered_token"
     * → Signature verification fails during username extraction
     * → Exception thrown, username = null
     * → Authentication NOT set
     * → Returns 401 for protected endpoints
     * 
     * @param request The incoming HTTP request
     * @param response The HTTP response (can be used to set headers/status)
     * @param filterChain Chain of filters to continue processing
     * @throws ServletException if servlet error occurs
     * @throws IOException if I/O error occurs
     */
    @Override
    protected void doFilterInternal(HttpServletRequest request, HttpServletResponse response, FilterChain filterChain)
            throws ServletException, IOException {
        
        // Step 1: Extract Authorization header from request
        // Example: "Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
        String authHeader = request.getHeader("Authorization");
        String token = null;
        String username = null;
        
        // Step 2: Check if header exists and has correct format
        if(authHeader != null && authHeader.startsWith("Bearer ")){
            // Extract token by removing "Bearer " prefix (7 characters)
            token = authHeader.substring(7);
            
            // Step 3: Extract username from JWT payload
            // JWT structure: header.payload.signature
            // Payload contains: {sub: "username", iat: ..., exp: ...}
            username = jwtUtils.extractUsername(token);
        }

        // Step 4: Authenticate if username extracted and not already authenticated
        // SecurityContextHolder.getContext().getAuthentication() == null means:
        // - No authentication set for this request yet
        // - Prevents re-authenticating if already done
        if(username != null && SecurityContextHolder.getContext().getAuthentication() == null){
            
            // Step 5: Load full user details from database
            // This ensures user still exists and gets their current roles/permissions
            UserDetails userDetails = customUserDetailsService.loadUserByUsername(username);

            // Step 6: Validate JWT token
            // Checks: username matches, token not expired, signature valid
            if(jwtUtils.validate(userDetails,username,token)){
                
                // Step 7: Create authentication token and set in SecurityContext
                // This tells Spring Security who the authenticated user is
                // UsernamePasswordAuthenticationToken parameters:
                // - principal: the user (UserDetails)
                // - credentials: null (password not needed after initial login)
                // - authorities: user's roles/permissions (from UserDetails)
                SecurityContextHolder.getContext().setAuthentication(
                    new UsernamePasswordAuthenticationToken(userDetails, null, userDetails.getAuthorities())
                );
            }
            // If validation fails, authentication is NOT set
            // Spring Security will deny access to protected endpoints
        }

        // Step 8: Continue to next filter in chain
        // Whether authenticated or not, let request continue
        // SecurityFilterChain will enforce authorization rules
        filterChain.doFilter(request, response);
    }
    
}

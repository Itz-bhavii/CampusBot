package com.bhavesh.campusbot.Utils;

import java.util.Date;

import javax.crypto.SecretKey;

import org.springframework.security.core.userdetails.UserDetails;
import org.springframework.stereotype.Component;

import io.jsonwebtoken.Claims;
import io.jsonwebtoken.Jwts;
import io.jsonwebtoken.SignatureAlgorithm;
import io.jsonwebtoken.security.Keys;

/**
 * Utility class for JWT (JSON Web Token) operations.
 * Handles token generation, validation, and claims extraction.
 * 
 * JWT BASICS:
 * JWT is a secure way to transmit information as a JSON object.
 * Structure: header.payload.signature (3 parts separated by dots)
 * 
 * Example JWT:
 * eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJqb2huIiwiaWF0IjoxNjE2MjM5MDIyfQ.SflKxwRJSMeKKF2QT4fwpMeJf36POk6yJV_adQssw5c
 * 
 * Part 1 (header): {"alg":"HS256","typ":"JWT"} → algorithm and type
 * Part 2 (payload): {"sub":"john","iat":1616239022,"exp":1616242622} → data/claims
 * Part 3 (signature): HMAC-SHA256 signature to verify authenticity
 * 
 * WHY JWT:
 * - Stateless: server doesn't store sessions, all info is in the token
 * - Scalable: any server can validate token without shared session storage
 * - Secure: signature prevents tampering
 * - Self-contained: token includes user identity and claims
 * 
 * CAMPUSBOT JWT FLOW:
 * 1. User logs in with username/password
 * 2. generateToken() creates JWT containing username
 * 3. Token sent to user
 * 4. User stores token and sends it with every request
 * 5. JwtAuthFilter extracts username from token
 * 6. validate() ensures token is authentic and not expired
 * 7. User is authenticated based on token
 */
@Component
public class JwtUtils {
    
    // Secret key for signing tokens - MUST be kept secret!
    // In production, load from environment variables, not hardcode
    // Must be at least 256 bits (32 characters) for HS256 algorithm
    private final String SECRET = "my-secret-is-long-enough-to-become-the-secret-key-123456789!@#";

    // Cryptographic key generated from secret string
    // Used for both signing (creating signature) and verification (checking signature)
    private final SecretKey key = Keys.hmacShaKeyFor(SECRET.getBytes());

    // Token expiration time: 20 hours in milliseconds
    // 1000ms * 60s * 60min * 20hr = 72,000,000ms
    // After 20 hours, token expires and user must login again
    private final long EXPIRATION_TIME = 1000*60*60*20; //20 hours

    /**
     * Generates a JWT token for a given username.
     * This is called after successful login to create the authentication token.
     * 
     * TOKEN STRUCTURE CREATED:
     * Header: {"alg":"HS256","typ":"JWT"}
     * Payload: {
     *   "sub": "username",           ← subject (who the token is for)
     *   "iat": 1638360000,            ← issued at (when token was created)
     *   "exp": 1638432000             ← expiration (when token expires)
     * }
     * Signature: HMACSHA256(header + payload, secret_key)
     * 
     * PROCESS:
     * 1. Create new JWT builder
     * 2. Set subject (username) - identifies who this token belongs to
     * 3. Set issued-at time (current time) - when token was created
     * 4. Set expiration time (current time + 20 hours) - when token becomes invalid
     * 5. Sign with secret key using HS256 algorithm - creates signature
     * 6. Compact into string format (header.payload.signature)
     * 
     * SECURITY:
     * - Signature ensures token hasn't been modified
     * - If someone changes username in payload, signature won't match
     * - Only server with secret key can create valid tokens
     * - Expiration ensures stolen tokens eventually become useless
     * 
     * USAGE EXAMPLE:
     * User "john" logs in successfully
     * → generateToken("john")
     * → Returns: "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
     * → Controller sends this token to frontend
     * → Frontend stores and includes in future requests
     * 
     * @param username The username to include in the token
     * @return JWT token string (Base64-encoded header.payload.signature)
     */
    public String generateToken(String username){
        return Jwts.builder()
            .setSubject(username)                                                  // Who this token is for
            .setIssuedAt(new Date())                                              // When created
            .setExpiration(new Date(System.currentTimeMillis() + EXPIRATION_TIME)) // When expires
            .signWith(key,SignatureAlgorithm.HS256)                               // Sign with secret key
            .compact();                                                            // Build final token string
    }

    /**
     * Extracts the username from a JWT token.
     * Used by JwtAuthFilter to identify who is making the request.
     * 
     * EXTRACTION PROCESS:
     * 1. Parse and verify token signature
     * 2. If signature invalid: throw exception (token tampered)
     * 3. If signature valid: extract payload (claims)
     * 4. Get "subject" claim from payload
     * 5. Return subject (which contains username)
     * 
     * EXAMPLE:
     * Token payload: {"sub":"john","iat":1638360000,"exp":1638432000}
     * → extractUsername(token)
     * → Returns: "john"
     * 
     * SECURITY:
     * - Automatically verifies signature before extracting
     * - If token modified: signature fails, exception thrown
     * - Ensures username came from a legitimate token
     * 
     * @param token The JWT token string
     * @return Username stored in the token's subject claim
     * @throws JwtException if token is invalid or tampered
     */
    public String extractUsername(String token) {
        Claims payload = extractPayload(token);  // Get all claims from token
        return payload.getSubject();              // Return "sub" claim (username)
    }

    /**
     * Extracts all claims (payload data) from a JWT token.
     * This is a private helper method used by other methods.
     * 
     * PARSING PROCESS:
     * 1. Create JWT parser
     * 2. Set verification key (to check signature)
     * 3. Build parser
     * 4. Parse the signed token
     * 5. Verify signature matches payload
     * 6. If valid: return payload (Claims object)
     * 7. If invalid: throw exception
     * 
     * CLAIMS OBJECT:
     * Claims is a Map containing:
     * - "sub" (subject): username
     * - "iat" (issued at): creation timestamp
     * - "exp" (expiration): expiry timestamp
     * - Any custom claims we add
     * 
     * VERIFICATION:
     * - Uses the same secret key used for signing
     * - Computes signature of header + payload
     * - Compares with signature in token
     * - If match: token is authentic
     * - If no match: token was tampered with
     * 
     * @param token The JWT token to parse
     * @return Claims object containing all payload data
     * @throws JwtException if signature verification fails
     */
    private Claims extractPayload(String token){
        return Jwts.parser()
                .verifyWith(key)                    // Set key for signature verification
                .build()                             // Build parser
                .parseSignedClaims(token)           // Parse and verify token
                .getPayload();                       // Extract payload (claims)
    }

    /**
     * Validates a JWT token to ensure it's authentic and not expired.
     * This is the critical security check that happens on EVERY request.
     * 
     * VALIDATION CHECKS:
     * 1. USERNAME MATCH:
     *    - Username from token must match username from database
     *    - Prevents using token for different user
     *    - Example: token says "john" but trying to access "alice" → reject
     * 
     * 2. NOT EXPIRED:
     *    - Current time must be before expiration time
     *    - Ensures old/stolen tokens can't be used forever
     *    - Example: token created at 10:00, expires 06:00 next day
     *      * At 05:00 next day: valid ✓
     *      * At 07:00 next day: expired ✗
     * 
     * 3. SIGNATURE VALID (implicit):
     *    - extractPayload() already verified signature
     *    - If we reach this method, signature was valid
     *    - Tampered tokens fail during username extraction
     * 
     * VALIDATION FLOW:
     * Token arrives → extractUsername() verifies signature → load user from DB
     * → validate() checks username match and expiration
     * 
     * SECURITY IMPLICATIONS:
     * - Both checks must pass for token to be valid
     * - If either fails: user is NOT authenticated
     * - Protected endpoints will return 401 Unauthorized
     * 
     * WHY CHECK USERNAME MATCH:
     * Prevents token reuse attacks:
     * - Attacker intercepts John's token
     * - Attacker tries to use it to access Alice's data
     * - Token username = "john", requested user = "alice"
     * - Validation fails, access denied
     * 
     * WHY CHECK EXPIRATION:
     * Limits damage from stolen tokens:
     * - Token stolen on Monday
     * - Attacker can only use it for 20 hours
     * - After expiration, token is worthless
     * - User must login again to get new token
     * 
     * @param userDetails User details loaded from database
     * @param username Username extracted from JWT token
     * @param token The complete JWT token
     * @return true if token is valid (username matches AND not expired), false otherwise
     */
    public boolean validate(UserDetails userDetails, String username, String token) {
        // Check 1: Username from token matches username from database
        // Check 2: Token hasn't expired
        return username.equals(userDetails.getUsername()) && !isTokenExpired(token);
    }

    /**
     * Checks if a JWT token has expired.
     * Compares token's expiration time with current time.
     * 
     * EXPIRATION CHECK:
     * 1. Extract expiration timestamp from token
     * 2. Get current time
     * 3. If expiration < current time: expired (true)
     * 4. If expiration >= current time: valid (false)
     * 
     * EXAMPLE:
     * Token created: 2024-01-01 10:00:00
     * Token expires: 2024-01-02 06:00:00 (20 hours later)
     * 
     * At 2024-01-02 05:00:00:
     * - expirationDate = 06:00:00
     * - currentDate = 05:00:00
     * - 06:00:00 before 05:00:00? NO
     * - isTokenExpired = false (still valid)
     * 
     * At 2024-01-02 07:00:00:
     * - expirationDate = 06:00:00
     * - currentDate = 07:00:00
     * - 06:00:00 before 07:00:00? YES
     * - isTokenExpired = true (expired!)
     * 
     * @param token The JWT token to check
     * @return true if token is expired, false if still valid
     */
    private boolean isTokenExpired(String token){
        // Get expiration time from token and compare with current time
        return extractPayload(token).getExpiration().before(new Date());
    }
}

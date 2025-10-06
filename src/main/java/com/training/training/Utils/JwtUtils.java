package com.training.training.Utils;

import java.sql.Time;
import java.util.Date;

import javax.crypto.SecretKey;

import org.springframework.security.core.userdetails.UserDetails;
import org.springframework.stereotype.Component;

import io.jsonwebtoken.Claims;
import io.jsonwebtoken.Jwts;
import io.jsonwebtoken.SignatureAlgorithm;
import io.jsonwebtoken.security.Keys;

@Component
public class JwtUtils {
    private final String SECRET = "my-secret-is-long-enough-to-become-the-secret-key-123456789!@#";

    private final SecretKey key = Keys.hmacShaKeyFor(SECRET.getBytes());

    private final long EXPIRATION_TIME = 1000*60*60;

    public String generateToken(String username){
        return Jwts.builder()
            .setSubject(username)
            .setIssuedAt(new Date())
            .setExpiration(new Date(System.currentTimeMillis() + EXPIRATION_TIME))
            .signWith(key,SignatureAlgorithm.HS256)
            .compact();
    }

    public String extractUsername(String token) {
        Claims payload = extractPayload(token);
        return payload.getSubject();
    }

    private Claims extractPayload(String token){
        return Jwts.parser()
                .verifyWith(key)
                .build()
                .parseSignedClaims(token)
                .getPayload();
    }

    public boolean validate(UserDetails userDetails, String username, String token) {
        return username.equals(userDetails.getUsername()) && !isTokenExpired(token);
    }

    private boolean isTokenExpired(String token){
        return extractPayload(token).getExpiration().before(new Date());
    }
}

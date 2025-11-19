package com.bhavesh.campusbot.Services;

import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.security.core.userdetails.UserDetails;
import org.springframework.security.core.userdetails.UserDetailsService;
import org.springframework.security.core.userdetails.UsernameNotFoundException;
import org.springframework.stereotype.Service;

import com.bhavesh.campusbot.Entities.Users;
import com.bhavesh.campusbot.Repositorys.UserDetailsRepository;

/**
 * Custom implementation of Spring Security's UserDetailsService.
 * This service is used by Spring Security during authentication to load user details from the database.
 * 
 * AUTHENTICATION FLOW:
 * 1. User sends login credentials (username + password) to /api/authenticate/login endpoint
 * 2. Spring Security's AuthenticationManager calls this service to load user details
 * 3. This service queries the database to find the user by username
 * 4. Returns the User entity which implements UserDetails interface
 * 5. Spring Security then compares the password with the stored hashed password
 * 6. If successful, authentication completes and JWT token is generated
 * 
 * This acts as the bridge between Spring Security framework and our database.
 */
@Service
public class CustomUserDetailsService implements UserDetailsService {

    // Repository to access user data from database
    @Autowired
    UserDetailsRepository userDetailsRepository;

    /**
     * Core method called by Spring Security to load user by username.
     * This is invoked during authentication (login) and JWT validation.
     * 
     * FLOW:
     * 1. Receives username from authentication attempt
     * 2. Queries database using UserDetailsRepository.findByUsername()
     * 3. If user exists: returns User entity (which implements UserDetails)
     * 4. If user doesn't exist: throws UsernameNotFoundException
     * 5. Spring Security uses the returned UserDetails to:
     *    - Compare password during login
     *    - Check user roles/authorities for authorization
     * 
     * @param username The username to look up in the database
     * @return UserDetails object containing user info (username, password, roles)
     * @throws UsernameNotFoundException if no user found with given username
     */
    @Override
    public UserDetails loadUserByUsername(String username) throws UsernameNotFoundException {
        // Query database for user - throw exception if not found
        Users user = userDetailsRepository.findByUsername(username).orElseThrow(()->new UsernameNotFoundException("User Not Found"));
        // Debug log showing user loaded with their assigned authorities/roles
        System.out.println(">>> Loading user '" + user.getUsername() + "' with authorities: " + user.getAuthorities());

        return user;
    }   

    
}

package com.bhavesh.campusbot.Services;

import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.security.core.userdetails.UserDetails;
import org.springframework.security.core.userdetails.UserDetailsService;
import org.springframework.security.core.userdetails.UsernameNotFoundException;
import org.springframework.stereotype.Service;

import com.bhavesh.campusbot.Entities.Users;
import com.bhavesh.campusbot.Repositorys.UserDetailsRepository;

@Service
public class CustomUserDetailsService implements UserDetailsService {

    @Autowired
    UserDetailsRepository userDetailsRepository;

    @Override
    public UserDetails loadUserByUsername(String username) throws UsernameNotFoundException {
        Users user = userDetailsRepository.findByUsername(username).orElseThrow(()->new UsernameNotFoundException("User Not Found"));
        System.out.println(">>> Loading user '" + user.getUsername() + "' with authorities: " + user.getAuthorities());

        return user;
    }   

    
}

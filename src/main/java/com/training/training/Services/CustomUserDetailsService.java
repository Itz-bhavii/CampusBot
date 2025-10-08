package com.training.training.Services;

import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.security.core.userdetails.UserDetails;
import org.springframework.security.core.userdetails.UserDetailsService;
import org.springframework.security.core.userdetails.UsernameNotFoundException;
import org.springframework.stereotype.Service;

import com.training.training.Entities.Users;
import com.training.training.Repositorys.UserDetailsRepository;

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

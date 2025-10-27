package com.bhavesh.campusbot.Controllers;

import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.security.authentication.AuthenticationManager;
import org.springframework.security.authentication.UsernamePasswordAuthenticationToken;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;

import com.bhavesh.campusbot.DTO.JwtAuthDTO;
import com.bhavesh.campusbot.Utils.JwtUtils;

@RestController
@RequestMapping("/api")
public class AuthController {
    @Autowired
    AuthenticationManager authenticationManager;

    @Autowired
    JwtUtils jwtUtils;
    
    @PostMapping("/authenticate")
    public String generateToken(@RequestBody JwtAuthDTO details){
        authenticationManager.authenticate(new UsernamePasswordAuthenticationToken(details.getUsername(), details.getPassword()));

        String token = jwtUtils.generateToken(details.getUsername());
        return token;
    }
}

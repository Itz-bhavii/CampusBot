package com.training.training.Controllers;

import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.security.authentication.AuthenticationManager;
import org.springframework.security.authentication.UsernamePasswordAuthenticationToken;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;

import com.training.training.DTO.JwtAuthDTO;
import com.training.training.Utils.JwtUtils;

@RestController
@RequestMapping("/api")
public class AuthController {
    @Autowired
    AuthenticationManager authenticationManager;

    @Autowired
    JwtUtils jwtUtils;
    
    @PostMapping("/authenticate")
    public String generateToken(@RequestBody JwtAuthDTO details){
        try{
            authenticationManager.authenticate(new UsernamePasswordAuthenticationToken(details.getUsername(), details.getPassword()));

            String token = jwtUtils.generateToken(details.getUsername());
            return token;


        }catch(Exception e){
            throw e;
        }
    }
}

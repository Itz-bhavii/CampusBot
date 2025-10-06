package com.training.training.Services;

import org.springframework.boot.CommandLineRunner;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Profile;
import org.springframework.security.crypto.password.PasswordEncoder;
import org.springframework.stereotype.Component;

import com.training.training.Entities.Users;
import com.training.training.Repositorys.UserDetailsRepository;

@Component
@Profile("!test")
public class DefaultAdminInitializer {
    @Bean
    public CommandLineRunner commandLineRunner(UserDetailsRepository userDetailsRepository,PasswordEncoder passwordEncoder){
        return args->{
            if(userDetailsRepository.findByUsername("admin").isEmpty()){
                Users admin = new Users();
                admin.setUsername("admin");
                admin.setPassword(passwordEncoder.encode("admin1234"));
                admin.setRole("ROLE_ADMIN");
                userDetailsRepository.save(admin);
                System.out.println("Default Admin Created With admin password");
            }
        };
    }
}

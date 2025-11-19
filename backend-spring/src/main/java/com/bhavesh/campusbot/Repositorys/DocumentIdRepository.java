package com.bhavesh.campusbot.Repositorys;

import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.stereotype.Repository;

import com.bhavesh.campusbot.Entities.Document;

@Repository
public interface DocumentIdRepository extends JpaRepository<Document,String>{
    
}

package com.bhavesh.campusbot.Entities;

import java.time.Instant;

import jakarta.persistence.Column;
import jakarta.persistence.Entity;
import jakarta.persistence.Id;
import jakarta.persistence.Table;
import lombok.AllArgsConstructor;
import lombok.Data;
import lombok.NoArgsConstructor;

@Entity
@Data
@NoArgsConstructor
@AllArgsConstructor
@Table(name = "documents")  
public class Document {
    @Id
    @Column(columnDefinition = "TEXT", nullable = false)
    private String fileHash;
    
    @Column(columnDefinition = "TEXT", nullable = false)
    private String filename;
    
    @Column(columnDefinition = "TEXT", nullable = false)
    private String uploadedBy;  

    @Column(nullable = false)
    private Instant uploadedDate;  // TIMESTAMPTZ
    
    @Column(nullable = false)
    private boolean isProcessed;  
}

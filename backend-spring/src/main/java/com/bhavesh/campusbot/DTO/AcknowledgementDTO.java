package com.bhavesh.campusbot.DTO;

import lombok.Data;

@Data
public class AcknowledgementDTO {
    private String documentId;
    private String documentName;
    private boolean processed;


}

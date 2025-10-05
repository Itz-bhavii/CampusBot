package com.training.training.Entities;

import lombok.NoArgsConstructor;

@NoArgsConstructor
public class ContentOfFileFromFlask {
    String content;

    public String getcontent() {
        return content;
    }

    public void setcontent(String content) {
        this.content = content;
    }
}

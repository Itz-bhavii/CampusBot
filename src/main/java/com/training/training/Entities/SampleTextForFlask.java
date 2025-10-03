package com.training.training.Entities;

import lombok.NoArgsConstructor;

@NoArgsConstructor
public class SampleTextForFlask {
    String text;

    public String getText() {
        return text;
    }

    public void setText(String text) {
        this.text = text;
    }
}

package com.bhavesh.campusbot.services;

import static org.assertj.core.api.Assertions.assertThat;
import static org.mockito.ArgumentMatchers.any;
import static org.mockito.ArgumentMatchers.eq;
import static org.mockito.Mockito.when;

import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.extension.ExtendWith;
import org.mockito.InjectMocks;
import org.mockito.Mock;
import org.mockito.junit.jupiter.MockitoExtension;
import org.springframework.mock.web.MockMultipartFile;
import org.springframework.web.client.RestTemplate;

import com.bhavesh.campusbot.DTO.ContentDTO;
import com.bhavesh.campusbot.DTO.PathDTO;
import com.bhavesh.campusbot.Services.FileStorageService;
import com.bhavesh.campusbot.Services.IngestionService;
import com.bhavesh.campusbot.Services.SenderMessageMQService;

@ExtendWith(MockitoExtension.class)
public class IngestionServiceTest {
    @Mock
    RestTemplate restTemplate;

    @Mock
    FileStorageService fileStorageService;

    @Mock // Add this
    SenderMessageMQService senderMessageMQService;

    @InjectMocks
    IngestionService ingestionService;


    @Test
    void getFileShouldPass(){

        ContentDTO expectedContent = new ContentDTO();
        expectedContent.setcontent("expected content");

        MockMultipartFile mockFile = new MockMultipartFile("file", "test.txt","text/plain","hello world".getBytes());

        String expectedPath = "D:/Temp/uploads/test.txt";
        when(fileStorageService.storeFileInMinioAndReturnPath(mockFile)).thenReturn(expectedPath);

        // when(restTemplate.postForObject(eq("http://127.0.0.1:5000/ingest"),any(PathDTO.class), eq(ContentDTO.class))).thenReturn(expectedContent);

        // ContentDTO ans = ingestionService.getFile(mockFile);
        // assertThat(ans.getcontent()).isEqualTo(expectedContent.getcontent());
        boolean ans = ingestionService.getFile(mockFile);
        assertThat(ans).isEqualTo(true);

    }

    @Test
    void getImageShouldPass(){
        ContentDTO expectedContent = new ContentDTO();
        expectedContent.setcontent("this is expected contnent");

        MockMultipartFile mockImage = new MockMultipartFile("img", "img.jpg","text/plain","imagedata".getBytes());
        String expectedPath = "D:/Temp/uploads/img.jpg";

        when(fileStorageService.storeFileInMinioAndReturnPath(mockImage)).thenReturn(expectedPath);

        when(restTemplate.postForObject(eq("http://127.0.0.1:5000/ingest-image"),any(PathDTO.class), eq(ContentDTO.class))).thenReturn(expectedContent);

        ContentDTO ans = ingestionService.getImage(mockImage);
        assertThat(ans.getcontent()).isEqualTo(expectedContent.getcontent());
    }
}

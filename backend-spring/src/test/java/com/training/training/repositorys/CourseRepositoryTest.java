package com.training.training.repositorys;

import org.junit.jupiter.api.Disabled;
import org.junit.jupiter.api.Test;
import org.assertj.core.api.Assertions;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.test.context.SpringBootTest;
import org.springframework.boot.test.mock.mockito.MockBean;
import org.springframework.test.context.ActiveProfiles;
import org.springframework.test.context.DynamicPropertyRegistry;
import org.springframework.test.context.DynamicPropertySource;
import org.testcontainers.containers.PostgreSQLContainer;
import org.testcontainers.junit.jupiter.Container;
import org.testcontainers.junit.jupiter.Testcontainers;

import com.training.training.Entities.Course;
import com.training.training.Repositorys.CourseRepository;
import com.training.training.Services.DefaultAdminInitializer;

@Disabled
@Testcontainers
@SpringBootTest
@ActiveProfiles("test")
public class CourseRepositoryTest {
    

    @Container
    static PostgreSQLContainer<?> postgres = new PostgreSQLContainer<>("postgres:15-alpine");

    @DynamicPropertySource
    static void configureProperties(DynamicPropertyRegistry registry) {
        registry.add("spring.datasource.url", postgres::getJdbcUrl);
        registry.add("spring.datasource.username", postgres::getUsername);
        registry.add("spring.datasource.password", postgres::getPassword);
        registry.add("spring.jpa.hibernate.ddl-auto", () -> "create-drop");
    }

    @Autowired
    private CourseRepository courseRepository;

    @Test
    public void saveAndRetrieveCourseSuccessfully(){
        Course course = new Course();
        course.setName("testing");
        course.setInstructorName("testing");
         
        Course savedCourse = courseRepository.save(course);

        Assertions.assertThat(savedCourse).isNotNull();
        Assertions.assertThat(savedCourse.getId()).isEqualTo(course.getId());
    }
}

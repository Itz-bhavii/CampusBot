package com.training.training.services;

import static org.mockito.ArgumentMatchers.any;
import static org.mockito.ArgumentMatchers.anyInt;
import static org.mockito.Mockito.times;
import static org.mockito.Mockito.when;

import java.util.Optional;

import org.junit.jupiter.api.Assertions;
import org.junit.jupiter.api.Disabled;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.extension.ExtendWith;
import org.mockito.InjectMocks;
import org.mockito.Mock;
import org.mockito.Mockito;
import org.mockito.junit.jupiter.MockitoExtension;
import org.mockito.junit.jupiter.MockitoSettings;
import org.mockito.quality.Strictness;

import static org.assertj.core.api.Assertions.assertThat;
import com.training.training.Entities.Course;
import com.training.training.Exceptions.ResourceNotFoundException;
import com.training.training.Repositorys.CourseRepository;
import com.training.training.Services.CourseService;


@ExtendWith(MockitoExtension.class)
public class CourseServiceTest {

    @Mock
    CourseRepository courseRepository;

    @InjectMocks
    CourseService courseService;

    @Test
    void saveCourseShouldRun(){
        Course course = new Course();
        course.setId(1);
        Mockito.when(courseRepository.save(course)).thenReturn(course);
        Course addedCourse = courseService.save(course);
        Assertions.assertEquals(1, addedCourse.getId());
    }
    
    @Test
    void getCourseByIdShouldSuccess(){
        Course course = new Course();
        course.setId(1);
        Mockito.when(courseRepository.findById(course.getId())).thenReturn(Optional.of(course));

        Optional<Course> returnedCourse = courseService.getCourseById(course.getId());
        Assertions.assertEquals(course.getId(), returnedCourse.get().getId());
    }
    
    @Test
    void getCourseByIdShouldFail(){
        Course course = new Course();
        course.setId(1);
        
        Mockito.when(courseRepository.findById(anyInt())).thenReturn(Optional.empty());
        
        Assertions.assertThrows(ResourceNotFoundException.class, ()->{
            courseService.getCourseById(course.getId());
        });
    }
    
    @Test
    void deleteCourseByIdShouldPass(){  
        Course course = new Course();
        course.setId(1);
        Mockito.doNothing().when(courseRepository).delete(course);
        Mockito.when(courseRepository.findById(1)).thenReturn(Optional.of(course));
        courseService.deleteCourseById(1);
        Mockito.verify(courseRepository,times(1)).delete(course);
    }
    
    @Test
    void deleteCourseByIdShouldFail(){
        Course course = new Course();
        course.setId(1);
        when(courseRepository.findById(anyInt())).thenReturn(Optional.empty());
        Assertions.assertThrows(ResourceNotFoundException.class, ()->{
            courseService.deleteCourseById(1);
        });
    }
    
    @Test
    void updateCourseByIdShould() {
        
        Course existingCourse = new Course(1, "Old Name", "Old Instructor");
        
        Course newData = new Course(null, "New Name", "New Instructor");

        when(courseRepository.findById(1)).thenReturn(Optional.of(existingCourse));

        when(courseRepository.save(any(Course.class))).thenReturn(newData);

        Course updatedCourse = courseService.updateCourseById(newData, 1);

        assertThat(updatedCourse).isNotNull();
        assertThat(updatedCourse.getName()).isEqualTo("New Name");
        assertThat(updatedCourse.getInstructorName()).isEqualTo("New Instructor");

    }

    
    
}

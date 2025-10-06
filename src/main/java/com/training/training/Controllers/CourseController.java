package com.training.training.Controllers;

import java.util.List;
import java.util.Optional;

import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;

import com.training.training.DTO.ContentDTO;
import com.training.training.Entities.Course;
import com.training.training.Services.CourseService;
import com.training.training.Services.IngestionService;


@RestController
@RequestMapping("/api")
public class CourseController {
    @Autowired
    CourseService courseService;

    @PostMapping("/courses")
    public ResponseEntity<Course> saveCourse(@RequestBody Course course){
        Course newCourse = courseService.save(course);
        return new ResponseEntity<>(newCourse,HttpStatus.CREATED);
    }

    @GetMapping("/courses")
    public ResponseEntity<List<Course>> getAllCourses(){
        return ResponseEntity.ok(courseService.getAllCourses());
    }

    @GetMapping("/courses/{id}")
    public ResponseEntity<Course> getCourseById(@PathVariable Integer id){
        Optional<Course> courseOptional = courseService.getCourseById(id);
        if(courseOptional.isPresent()){
            return new ResponseEntity<>(courseOptional.get(),HttpStatus.OK); 
        }
        else{
            return new ResponseEntity<>(HttpStatus.NOT_FOUND);
        }
    }

    @PutMapping("/courses/{id}")
    public ResponseEntity<Course> updateCourseById(@RequestBody Course newCourse,@PathVariable Integer id){
       return new ResponseEntity<>(courseService.updateCourseById(newCourse,id),HttpStatus.OK);
    }

    @DeleteMapping("courses/{id}")
    public ResponseEntity<?> deleteCourseById(@PathVariable Integer id){
        courseService.deleteCourseById(id);
        return new ResponseEntity<>(HttpStatus.NO_CONTENT);
    }

}

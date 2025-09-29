package com.training.training.Controllers;

import java.util.List;

import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;

import com.training.training.Entities.Course;
import com.training.training.Services.CourseService;

@RestController
@RequestMapping("/api")
public class CourseController {
    @Autowired
    CourseService courseService;

    @PostMapping("/courses")
    public ResponseEntity<Course> saveCourse(@RequestBody Course course){
        Course newCourse = courseService.save(course);
        return ResponseEntity.ok(newCourse);
    }

    @GetMapping("/courses")
    public List<Course> getAllCourses(){
        return courseService.getAllCourses();
    }

    @GetMapping("/courses/{id}")
    public Course getCourseById(@PathVariable Integer id){
        return courseService.getCourseById(id); 
    }

    @PutMapping("/courses/{id}")
    public Course updateCourseById(@RequestBody Course newCourse,@PathVariable Integer id){
        return courseService.updateCourseById(newCourse,id);
    }

    @DeleteMapping("courses/{id}")
    public void deleteCourseById(@PathVariable Integer id){
        courseService.deleteCourseById(id);
    }

}

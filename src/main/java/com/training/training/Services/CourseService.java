package com.training.training.Services;

import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.stereotype.Service;

import com.training.training.Entities.Course;
import com.training.training.Exceptions.ResourceNotFoundException;
import com.training.training.Repositorys.CourseRepository;

import java.util.List;
import java.util.Optional;

@Service
public class CourseService {
    @Autowired
    CourseRepository courseRepository;

    public Course save(Course course){
        return courseRepository.save(course);
    }

    public List<Course> getAllCourses(){
        return courseRepository.findAll();
    }

    public Optional<Course> getCourseById(Integer id) {
        Optional<Course> course = courseRepository.findById(id);
        if(!course.isPresent()){
            throw new ResourceNotFoundException("item not found");
        }
        return course;
    }

    public void deleteCourseById(Integer id){
        Course course = getCourseById(id).orElse(null);
        if(course != null){
            courseRepository.delete(course);
        }
        else{
            throw new ResourceNotFoundException("item not found");
        }
    }

    public Course updateCourseById(Course newCourse,Integer id){
        Course oldCourse = getCourseById(id).orElse(newCourse);
        oldCourse.setName(newCourse.getName().equals("") ? oldCourse.getName() : newCourse.getName());
        oldCourse.setInstructorName(newCourse.getInstructorName().equals("") ? oldCourse.getInstructorName() : newCourse.getInstructorName());
        return save(oldCourse);
    }
}

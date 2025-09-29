package com.training.training.Services;

import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.stereotype.Service;

import com.training.training.Entities.Course;
import com.training.training.Repositorys.CourseRepository;

import java.util.List;

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

    public Course getCourseById(Integer id) {
        return courseRepository.findCourseById(id);
    }

    public void deleteCourseById(Integer id){
        Course course = getCourseById(id);
        courseRepository.delete(course);
    }

    public Course updateCourseById(Course newCourse,Integer id){
        Course oldCourse = getCourseById(id);
        oldCourse.setName(newCourse.getName().equals("")? oldCourse.getName():newCourse.getName());
        oldCourse.setInstructorName(newCourse.getInstructorName().equals("")?oldCourse.getInstructorName():newCourse.getInstructorName());
        return save(oldCourse);
    }
}

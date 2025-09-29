package com.training.training.Repositorys;

import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.stereotype.Repository;

import com.training.training.Entities.Course;

@Repository
public interface CourseRepository extends JpaRepository<Course,Integer>{
    public Course findCourseById(Integer id);
}

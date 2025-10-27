package com.bhavesh.campusbot.Repositorys;

import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.stereotype.Repository;

import com.bhavesh.campusbot.Entities.Course;

@Repository
public interface CourseRepository extends JpaRepository<Course,Integer>{
    
}

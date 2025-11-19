package com.bhavesh.campusbot.Services;

import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.stereotype.Service;

import com.bhavesh.campusbot.Entities.Course;
import com.bhavesh.campusbot.Exceptions.ResourceNotFoundException;
import com.bhavesh.campusbot.Repositorys.CourseRepository;

import java.util.List;
import java.util.Optional;

/**
 * Service layer for managing course information.
 * Provides CRUD (Create, Read, Update, Delete) operations for courses.
 * 
 * TYPICAL USE CASE:
 * - Admin uploads course documents which get stored with course information
 * - Users can query courses to find which documents are available
 * - Course metadata helps the AI provide context-aware responses
 */
@Service
public class CourseService {
    // Repository interface for database operations on Course entities
    @Autowired
    CourseRepository courseRepository;

    /**
     * Saves a course to the database.
     * Can be used for both creating new courses and updating existing ones.
     * 
     * @param course The Course entity to save
     * @return The saved Course entity (with generated ID if it was new)
     */
    public Course save(Course course){
        return courseRepository.save(course);
    }

    /**
     * Retrieves all courses from the database.
     * Used by frontend to display available courses to users.
     * 
     * @return List of all Course entities in the database
     */
    public List<Course> getAllCourses(){
        return courseRepository.findAll();
    }

    /**
     * Retrieves a specific course by its ID.
     * 
     * FLOW:
     * 1. Queries database for course with given ID
     * 2. If found: returns Optional containing the course
     * 3. If not found: throws ResourceNotFoundException
     * 
     * @param id The unique identifier of the course
     * @return Optional containing the Course if found
     * @throws ResourceNotFoundException if course with given ID doesn't exist
     */
    public Optional<Course> getCourseById(Integer id) {
        Optional<Course> course = courseRepository.findById(id);
        if(!course.isPresent()){
            throw new ResourceNotFoundException("item not found");
        }
        return course;
    }

    /**
     * Deletes a course from the database.
     * 
     * FLOW:
     * 1. Attempts to find course with given ID
     * 2. If course exists: deletes it from database
     * 3. If course doesn't exist: throws ResourceNotFoundException
     * 
     * @param id The unique identifier of the course to delete
     * @throws ResourceNotFoundException if course with given ID doesn't exist
     */
    public void deleteCourseById(Integer id){
        Course course = getCourseById(id).orElse(null);
        if(course != null){
            courseRepository.delete(course);
        }
        else{
            throw new ResourceNotFoundException("item not found");
        }
    }

    /**
     * Updates an existing course with new information.
     * 
     * PARTIAL UPDATE LOGIC:
     * - If new name is provided (not empty): updates the name
     * - If new name is empty: keeps the old name
     * - Same logic applies for instructor name
     * 
     * This allows for partial updates where only changed fields need to be sent.
     * 
     * FLOW:
     * 1. Retrieves existing course from database using ID
     * 2. Checks each field in newCourse:
     *    - If field is not empty: update old course with new value
     *    - If field is empty: keep old value
     * 3. Saves updated course back to database
     * 
     * @param newCourse Course object containing new values (may have empty fields)
     * @param id The ID of the course to update
     * @return The updated Course entity
     */
    public Course updateCourseById(Course newCourse,Integer id){
        Course oldCourse = getCourseById(id).orElse(newCourse);
        // Only update name if new name is provided
        oldCourse.setName(newCourse.getName().equals("") ? oldCourse.getName() : newCourse.getName());
        // Only update instructor name if new instructor name is provided
        oldCourse.setInstructorName(newCourse.getInstructorName().equals("") ? oldCourse.getInstructorName() : newCourse.getInstructorName());
        return save(oldCourse);
    }
}

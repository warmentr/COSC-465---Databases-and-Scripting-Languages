DROP TABLE IF EXISTS enrollment;
DROP TABLE IF EXISTS courses;
DROP TABLE IF EXISTS students;

-- Create Tables

CREATE TABLE students (
    student_id INTEGER PRIMARY KEY,
    name TEXT NOT NULL,
    major TEXT
);

CREATE TABLE courses (
    course_id INTEGER PRIMARY KEY,
    title TEXT NOT NULL,
    credits INTEGER
);

CREATE TABLE enrollment (
    student_id INTEGER,
    course_id INTEGER,
    PRIMARY KEY (student_id, course_id),
    FOREIGN KEY (student_id) REFERENCES students(student_id),
    FOREIGN KEY (course_id) REFERENCES courses(course_id)
);


-- ============================================================
-- Populate students
-- ============================================================

INSERT INTO students (student_id, name, major)
VALUES (1, 'Alice', 'CS');

INSERT INTO students (student_id, name, major)
VALUES (2, 'Bob', 'EE');

INSERT INTO students (student_id, name, major)
VALUES (3, 'Carol', 'CS');

INSERT INTO students (student_id, name, major)
VALUES (4, 'David', 'Math');


-- ============================================================
-- Populate courses
-- ============================================================

INSERT INTO courses (course_id, title, credits)
VALUES (101, 'Databases', 3);

INSERT INTO courses (course_id, title, credits)
VALUES (102, 'Python', 4);

INSERT INTO courses (course_id, title, credits)
VALUES (103, 'Software Eng', 3);


-- ============================================================
-- Populate enrollment
-- ============================================================

INSERT INTO enrollment (student_id, course_id)
VALUES (1, 101);

INSERT INTO enrollment (student_id, course_id)
VALUES (1, 103);

INSERT INTO enrollment (student_id, course_id)
VALUES (2, 101);

INSERT INTO enrollment (student_id, course_id)
VALUES (3, 102);


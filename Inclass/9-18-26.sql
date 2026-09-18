DROP VIEW IF EXISTS student_courses;
DROP VIEW IF EXISTS student_summary;

--1.
CREATE VIEW student_courses AS
SELECT s.student_id, s.name, c.course_id, c.title, c.credits
FROM students AS s
JOIN enrollment AS e 
    ON s.student_id = e.student_id
JOIN courses AS c
    ON e.course_id = c.course_id;

SELECT * FROM student_courses;

--2.
SELECT name, title
FROM student_courses
WHERE credits = 3
ORDER BY name, title;

--3.
INSERT INTO enrollment (student_id, course_id)
VALUES (4, 101);

SELECT * FROM student_courses
WHERE student_id = 4;

--4. 
CREATE VIEW student_summary AS
SELECT s.student_id, s.name, COUNT(e.course_id) AS course_count
FROM students AS s
LEFT JOIN enrollment as e 
    ON s.student_id = e.student_id
GROUP BY s.student_id;

SELECT * FROM student_summary;
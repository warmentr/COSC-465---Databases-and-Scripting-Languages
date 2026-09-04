
-- 1.
SELECT students.name, enrollment.course_id
FROM students
INNER JOIN enrollment ON students.student_id = enrollment.student_id;

--2.
SELECT s.name, c.title
FROM students AS s
INNER JOIN enrollment AS e ON s.student_id == e.student_id
INNER JOIN courses AS c ON e.course_id == c.course_id;

--3.
SELECT s.name, c.title
FROM students AS s
INNER JOIN enrollment AS e ON s.student_id == e.student_id
INNER JOIN courses AS c ON e.course_id == c.course_id
WHERE s.name == 'Alice';

--4.
SELECT s.name
FROM students AS s
INNER JOIN enrollment AS e ON s.student_id == e.student_id
INNER JOIN courses AS c ON e.course_id == c.course_id
WHERE c.title == 'Databases';

--5.
SELECT s.name, s.major, c.title, c.credits
FROM students AS s
INNER JOIN enrollment AS e ON s.student_id == e.student_id
INNER JOIN courses AS c ON e.course_id == c.course_id;

--6.
SELECT students.name, enrollment.course_id
FROM students
INNER JOIN enrollment;
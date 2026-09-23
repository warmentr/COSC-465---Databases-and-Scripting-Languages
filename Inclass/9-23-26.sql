--1. Insert and upsert
INSERT INTO students (student_id, name, major)
VALUES (5, 'Emma', 'CS');

INSERT INTO enrollment (student_id, course_id)
VALUES (5, 101);

INSERT INTO students (name, major)
VALUES ('Frank', 'Math');

SELECT student_id
FROM students
WHERE name = 'Frank';

INSERT INTO students(student_id, name, major)
VALUES(5, 'Emma', 'CS')
ON CONFLICT(student_id)
DO UPDATE SET
    name = excluded.name,
    major = excluded.major;

-- PRIMARY KEY does always mean automatically generated

--2. Update
SELECT * FROM students
WHERE student_id = 5;

UPDATE students
SET major = 'EE'
WHERE student_id = 5;

SELECT * FROM students
WHERE major = 'CS';

UPDATE students
set major = 'Computing'
WHERE major = 'CS';

-- updating several rows is not always a mistake

--3. Delete
SELECT * FROM enrollment
WHERE student_id = 5 AND course_id = 101;

DELETE FROM enrollment
WHERE student_id = 5
    AND course_id = 101;

SELECT * FROM enrollment
WHERE student_id = 5 AND course_id = 101; -- should be blank

-- DELETE FROM enrollment; would delete every row from the table, but table still exists.
-- DROP TABLE would get rid of the table so that it doesn't exists.
-- It's a safe habit to verify which rows will be deleted or updated before deleting or updating them

--4. result
SELECT * FROM students;
SELECT * FROM enrollment;
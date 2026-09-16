BEGIN;

DELETE FROM enrollment
WHERE student_id = 1
    AND course_id = 103;

INSERT INTO enrollment (student_id, course_id)
VALUES (1, 102);

SELECT * FROM enrollment;
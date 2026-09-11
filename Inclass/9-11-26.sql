-- 1.
SELECT student_id
FROM enrollment
WHERE course_id IN (
    SELECT course_id
    FROM courses
    WHERE title = 'Databases'
);

-- 2.
SELECT s.name
FROM students AS s
WHERE s.student_id IN (
    SELECT e.student_id
    FROM enrollment AS e
    WHERE e.course_id IN (
        SELECT c.course_id
        FROM courses AS c
        WHERE c.credits = 3
    )
);

-- 3.
SELECT s.name
FROM students AS s
WHERE EXISTS (
    SELECT 1 FROM enrollment AS e
    WHERE e.student_id = s.student_id
);

-- 4.
SELECT s.name
FROM students AS s
WHERE NOT EXISTS (
    SELECT 1 FROM enrollment AS e
    WHERE e.student_id = s.student_id
);

-- 5.
WITH database_students AS (
    SELECT e.student_id
    FROM enrollment AS e
    JOIN courses AS c
        ON e.course_id = c.course_id
    WHERE c.title = 'Databases'
)
SELECT 
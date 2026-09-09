-- 1.
SELECT s.name, e.course_id
FROM students AS s
LEFT JOIN enrollment AS e 
    ON s.student_id = e.student_id;

-- 2.
SELECT s.name, c.title
FROM students AS s
LEFT JOIN enrollment AS e
    ON s.student_id = e.student_id
LEFT JOIN courses AS c
    ON e.course_id = c.course_id;

-- 3.
SELECT s.name
FROM students AS s
LEFT JOIN enrollment AS e
    ON s.student_id = e.student_id
WHERE e.course_id IS NULL;

-- 4.
SELECT c.title
FROM students AS s
LEFT JOIN enrollment AS e
    ON s.student_id = e.student_id
LEFT JOIN courses AS c
    ON e.course_id = c.course_id
WHERE s.name = 'Alice'

UNION

SELECT c.title
FROM students AS s
LEFT JOIN enrollment AS e
    ON s.student_id = e.student_id
LEFT JOIN courses AS c
    ON e.course_id = c.course_id
WHERE s.name = 'Bob';

-- 5.
SELECT c.title
FROM students AS s
LEFT JOIN enrollment AS e
    ON s.student_id = e.student_id
LEFT JOIN courses AS c
    ON e.course_id = c.course_id
WHERE s.name = 'Alice'

UNION ALL

SELECT c.title
FROM students AS s
LEFT JOIN enrollment AS e
    ON s.student_id = e.student_id
LEFT JOIN courses AS c
    ON e.course_id = c.course_id
WHERE s.name = 'Bob';

-- 6.
SELECT s.name, c.title
FROM students AS s
LEFT JOIN enrollment AS e
    ON s.student_id = e.student_id
LEFT JOIN courses AS c
    ON e.course_id = c.course_id
WHERE c.title = 'Databases';

--SELECT * FROM students;
--SELECT * FROM enrollment;
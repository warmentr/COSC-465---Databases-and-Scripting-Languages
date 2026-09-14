.mode box
.nullvalue NULL

--3.
SELECT s.name, 
    COUNT(e.course_id) AS course_count,
    CASE
        WHEN COUNT(e.course_id) = 0 THEN 'Not Enrolled'
        ELSE 'Enrolled'
    END AS status
FROM students AS s
LEFT JOIN enrollment as e
    ON s.student_id = e.student_id
GROUP BY s.student_id, s.name;
--1. SCAN

--2
EXPLAIN QUERY PLAN
SELECT *
FROM enrollment
WHERE course_id = 101;

--3
CREATE INDEX
idx_enrollment_course
ON enrollment(course_id);

--4
EXPLAIN QUERY PLAN
SELECT *
FROM enrollment
WHERE course_id = 101;
-- should produce SEARCH

--5
-- It does not guarantee index use as a query may not need the index

--6
-- best WHERE major = 'CS' AND name = 'Alice'
-- next WHERE major = 'CS'
-- last WHERE name = 'Alice'
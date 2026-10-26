PRAGMA foreign_keys = ON;

BEGIN;

-- Alice drops Software Eng
DELETE FROM enrollment
WHERE student_id = 1
  AND course_id = 103;

-- Alice enrolls in Python
INSERT INTO enrollment (student_id, course_id)
--VALUES (1000, 1002);
VALUES (1, 102);

COMMIT;

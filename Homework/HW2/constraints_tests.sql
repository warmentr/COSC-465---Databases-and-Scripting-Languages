.mode box
PRAGMA foreign_keys = ON;

-- tests

--1. expected to fail because of UNIQUE constraint
INSERT INTO attendees (name, email)
VALUES ('Alice2', 'alice@example.com');

--2. expected to fail because of NOT NULL constraint
INSERT INTO attendees (email)
VALUES ('noname@example.com');

--3.  expected to fail because of CHECK constraint capacity > 0
INSERT INTO events (title, capacity, fee)
VALUES ('Zero Capactiy Event', 0, 10.00);

--4.  expected to fail because of CHECK constraint fee >= 0
INSERT INTO events (title, capacity, fee)
VALUES ('Negative Fee Event', 10, -5.00);

--5. expected to fail because of FOREIGN KEY constraint
INSERT INTO registrations (attendee_id, event_id)
VALUES (999, 1);

--6. expected to fail because of FOREIGN KEY constraint
INSERT INTO registrations (attendee_id, event_id)
VALUES (1, 999);

--7. expected to fail because of UNIQUE constraint from primary keys
INSERT INTO registrations (attendee_id, event_id)
VALUES (1, 1);

--8. It will work
INSERT INTO attendees (name, email)
VALUES ('David Green', 'david@example.com');

SELECT * FROM attendees
WHERE email = 'david@example.com';
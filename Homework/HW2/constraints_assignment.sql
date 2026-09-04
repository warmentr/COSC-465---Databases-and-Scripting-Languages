.mode box
PRAGMA foreign_keys = ON;

-- Drop tables for repeat runs
DROP TABLE IF EXISTS registrations;
DROP TABLE IF EXISTS events;
DROP TABLE IF EXISTS attendees;

-- Create tables
CREATE TABLE attendees (
    attendee_id INTEGER PRIMARY KEY,
    name TEXT NOT NULL,
    email TEXT UNIQUE NOT NULL,
    status TEXT DEFAULT 'active'
);

CREATE TABLE events (
    event_id INTEGER PRIMARY KEY,
    title TEXT NOT NULL,
    capacity INTEGER NOT NULL CHECK (capacity>0),
    fee REAL CHECK (fee >= 0),
    status TEXT DEFAULT 'open'
);

CREATE TABLE registrations (
    attendee_id INTEGER,
    event_id INTEGER,

    FOREIGN KEY (attendee_id) REFERENCES attendees(attendee_id),
    FOREIGN KEY (event_id) REFERENCES events(event_id)
    PRIMARY KEY (attendee_id, event_id)
);

-- populate tables display as you go
INSERT INTO attendees(name, email)
VALUES
    ('Alice Smith', 'alice@example.com');

INSERT INTO attendees(name, email, status)
VALUES
    ('Bob Jones', 'bob@example.com', 'inactive'),
    ('Carol Brown', 'carol@example.com', 'active');

SELECT * FROM attendees;

INSERT INTO events(title, capacity, fee)
VALUES
        ('Database Day', '100', '0.00');

INSERT INTO events(title, capacity, fee, status)
VALUES
    ('Python Night', '50', '10.00', 'open'),
    ('SQL Workshop', '25', '15.00', 'open');

SELECT * FROM events;

INSERT INTO registrations (attendee_id, event_id)
SELECT a.attendee_id, e.event_id
FROM (
    SELECT column1 AS name, column2 AS title
    FROM (VALUES
        ('Alice Smith', 'Database Day'),
        ('Alice Smith', 'SQL Workshop'),
        ('Bob Jones', 'Database Day'),
        ('Carol Brown', 'Python Night')
    )
) AS pairs
JOIN attendees AS a ON a.name = pairs.name
JOIN events AS e ON e.title = pairs.title;

SELECT * FROM registrations;
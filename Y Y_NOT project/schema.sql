-- drop statements to keep clean
DROP TABLE IF EXISTS Users
DROP TABLE IF EXISTS Posts
DROP TABLE IF EXISTS Follows
DROP TABLE IF EXISTS Comments
DROP TABLE IF EXISTS Likes
DROP TABLE IF EXISTS Reports
DROP TABLE IF EXISTS Post_hashtags
DROP TABLE IF EXISTS Hashtags

-- Create tables
CREATE TABLE Users (
    UserID INTEGER PRIMARY KEY,
    Username TEXT UNIQUE,
    Email TEXT UNIQUE,
    CreatedAt TEXT,
    IsPrivate INTEGER DEFAULT 0,    -- 0 private, 1 public
    Role TEXT DEFAULT 'user'
);

CREATE TABLE Posts (
    PostID INTEGER PRIMARY KEY,
    UserID INTEGER NOT NULL,
    Content TEXT,
    CreatedAt TEXT,

    FOREIGN KEY(UserID) REFERENCES Users(UserID)
);

CREATE TABLE Follows (
    FollowerID INTEGER,
    FolloweeID INTEGER,
    Status TEXT NOT NULL,
    CreatedAt TEXT,

    FOREIGN KEY(FollowerID) REFERENCES Users(UserID),
    FOREIGN KEY(FolloweeID) REFERENCES Users(UserID),
    PRIMARY KEY(FollowerID, FolloweeID)
);

CREATE TABLE Comments ();

CREATE TABLE Likes ();

CREATE TABLE Reports ();

CREATE TABLE Post_hashtags ();

CREATE TABLE Hashtags ();
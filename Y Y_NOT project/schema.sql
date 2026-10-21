PRAGMA foreign_keys = ON;

-- drop statements to keep clean
DROP VIEW IF EXISTS TrendingHashtags;
DROP VIEW IF EXISTS ModerationQueue;
DROP VIEW IF EXISTS PendingFollowRequests;
DROP VIEW IF EXISTS FollowingFeed;
DROP VIEW IF EXISTS UserStats;
DROP VIEW IF EXISTS PostStats;

DROP TABLE IF EXISTS Post_hashtags;
DROP TABLE IF EXISTS Reports;
DROP TABLE IF EXISTS Likes;
DROP TABLE IF EXISTS Comments;
DROP TABLE IF EXISTS Follows;
DROP TABLE IF EXISTS Hashtags;
DROP TABLE IF EXISTS Posts;
DROP TABLE IF EXISTS Users;

-- Create tables
CREATE TABLE Users (
    UserID      INTEGER PRIMARY KEY,
    Username    TEXT NOT NULL UNIQUE,
    Email       TEXT NOT NULL UNIQUE,
    CreatedAt   TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%SZ','now')),   -- ISO 8601
    IsPrivate   INTEGER NOT NULL DEFAULT 1 CHECK (IsPrivate IN (0,1)),          -- 1 private, 0 public
    Role        TEXT NOT NULL DEFAULT 'user' CHECK (Role IN ('user', 'moderator', 'admin'))
);

CREATE TABLE Posts (
    PostID      INTEGER PRIMARY KEY,
    UserID      INTEGER NOT NULL,
    Content     TEXT NOT NULL,
    CreatedAt   TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%SZ','now')),

    FOREIGN KEY(UserID) REFERENCES Users(UserID)
);

CREATE TABLE Follows (
    FollowerID  INTEGER NOT NULL,
    FolloweeID  INTEGER NOT NULL,
    Status      TEXT NOT NULL DEFAULT 'pending' CHECK (Status IN ('pending', 'accepted')),
    CreatedAt   TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%SZ','now')),

    PRIMARY KEY(FollowerID, FolloweeID),
    FOREIGN KEY(FollowerID) REFERENCES Users(UserID),
    FOREIGN KEY(FolloweeID) REFERENCES Users(UserID),
    CHECK (FollowerID <> FolloweeID)
);

CREATE TABLE Comments (
    CommentID   INTEGER PRIMARY KEY,
    PostID      INTEGER NOT NULL,
    UserID      INTEGER NOT NULL,
    Body        TEXT NOT NULL,
    CreatedAt   TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%SZ','now')),

    FOREIGN KEY(PostID) REFERENCES Posts(PostID),
    FOREIGN KEY(UserID) REFERENCES Users(UserID)
);

CREATE TABLE Likes (
    LikeID      INTEGER PRIMARY KEY,
    UserID      INTEGER NOT NULL,
    PostID      INTEGER NOT NULL,
    CreatedAt   TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%SZ','now')),

    FOREIGN KEY(PostID) REFERENCES Posts(PostID),
    FOREIGN KEY(UserID) REFERENCES Users(UserID),
    UNIQUE (UserID, PostID)
);

CREATE TABLE Reports (
    ReportID    INTEGER PRIMARY KEY,
    PostID      INTEGER NOT NULL,
    ReporterID  INTEGER NOT NULL,
    Reason      TEXT NOT NULL,
    Status      TEXT NOT NULL DEFAULT 'open' CHECK (Status IN ('open', 'reviewed', 'dismissed')),
    CreatedAt   TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%SZ','now')),
    ReviewedBy  INTEGER,    -- Null until it is reviewed by moderator
    ReviewedAt  TEXT,

    FOREIGN KEY (PostID) REFERENCES Posts(PostID),
    FOREIGN KEY (ReporterID) REFERENCES Users(UserID),
    FOREIGN KEY (ReviewedBy) REFERENCES Users(UserID),
    UNIQUE (ReporterID, PostID),
    CHECK ((ReviewedBy IS NULL) = (ReviewedAt IS NULL)) -- so a report can't have a reviewer without a review time
);

CREATE TABLE Hashtags (
    HashtagID   INTEGER PRIMARY KEY,
    Tag         TEXT NOT NULL UNIQUE
);

CREATE TABLE Post_hashtags (
    PostID      INTEGER NOT NULL,
    HashtagID   INTEGER NOT NULL,

    PRIMARY KEY (PostID, HashtagID),
    FOREIGN KEY(PostID) REFERENCES Posts(PostID),
    FOREIGN KEY(HashtagID) REFERENCES Hashtags(HashtagID)
);

-- Useful Indexes
CREATE INDEX idx_post_user          ON Posts(UserID);
CREATE INDEX idx_comments_post      ON Comments(PostID);
CREATE INDEX idx_likes_post         ON Likes(PostID);
CREATE INDEX idx_follows_followee   ON Follows(FolloweeID);

-- potentially useful views

-- Each post with its author and like/comment counts.
CREATE VIEW PostStats AS
SELECT
    p.PostID,
    p.UserID,
    u.Username,
    p.Content,
    p.CreatedAt,
    (SELECT COUNT(*) FROM Likes    l WHERE l.PostID = p.PostID) AS LikeCount,
    (SELECT COUNT(*) FROM Comments c WHERE c.PostID = p.PostID) AS CommentCount
FROM Posts p
JOIN Users u ON u.UserID = p.UserID;

-- Profile numbers per user. Only accepted follows count.
CREATE VIEW UserStats AS
SELECT
    u.UserID,
    u.Username,
    u.IsPrivate,
    (SELECT COUNT(*) FROM Posts p   WHERE p.UserID = u.UserID)                              AS PostCount,
    (SELECT COUNT(*) FROM Follows f WHERE f.FolloweeID = u.UserID AND f.Status = 'accepted') AS FollowerCount,
    (SELECT COUNT(*) FROM Follows f WHERE f.FollowerID = u.UserID AND f.Status = 'accepted') AS FollowingCount
FROM Users u;

-- Posts from people a viewer follows.
CREATE VIEW FollowingFeed AS
SELECT
    f.FollowerID AS ViewerID,
    p.PostID,
    p.UserID     AS AuthorID,
    u.Username   AS AuthorUsername,
    p.Content,
    p.CreatedAt
FROM Follows f
JOIN Posts p ON p.UserID = f.FolloweeID
JOIN Users u ON u.UserID = p.UserID
WHERE f.Status = 'accepted';

-- Follow requests waiting on approval (mainly for private accounts):
CREATE VIEW PendingFollowRequests AS
SELECT
    f.FolloweeID,
    f.FollowerID,
    u.Username AS RequesterUsername,
    f.CreatedAt
FROM Follows f
JOIN Users u ON u.UserID = f.FollowerID
WHERE f.Status = 'pending';

-- Posts with open reports. Because of UNIQUE(ReporterID, PostID),
CREATE VIEW ModerationQueue AS
SELECT
    p.PostID,
    p.Content,
    au.Username      AS AuthorUsername,
    COUNT(*)         AS ReportCount,
    MIN(r.CreatedAt) AS FirstReportedAt,
    MAX(r.CreatedAt) AS LastReportedAt
FROM Reports r
JOIN Posts p  ON p.PostID  = r.PostID
JOIN Users au ON au.UserID = p.UserID
WHERE r.Status = 'open'
GROUP BY p.PostID, p.Content, au.Username;

-- Hashtag usage over the last 7 days. 'now' is evaluated each time you query it.
CREATE VIEW TrendingHashtags AS
SELECT
    h.HashtagID,
    h.Tag,
    COUNT(*) AS PostCount
FROM Hashtags h
JOIN Post_hashtags ph ON ph.HashtagID = h.HashtagID
JOIN Posts p          ON p.PostID     = ph.PostID
WHERE p.CreatedAt >= strftime('%Y-%m-%dT%H:%M:%SZ', 'now', '-7 days')
GROUP BY h.HashtagID, h.Tag;
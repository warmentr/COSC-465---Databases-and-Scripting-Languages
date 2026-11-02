-- Scenario: moderator mod_mira (UserID 6) removes the spam "giveaway" post (PostID 21).
-- Three related changes must succeed or fail together:
--   1. mark every open report on the post as reviewed (by the moderator, with a timestamp)
--   2. replace the post's content with a removal notice
--   3. detach the post from its hashtags so it stops showing up in tag pages

PRAGMA foreign_keys = ON;   -- must be set before BEGIN (it is ignored inside a transaction)

--- BEFORE: post 21 is in the moderation queue, has 2 hashtags, original content ---
SELECT PostID, ReportCount FROM ModerationQueue;
SELECT COUNT(*) AS HashtagLinks FROM Post_hashtags WHERE PostID = 21;
SELECT substr(Content, 1, 40) AS Content FROM Posts WHERE PostID = 21;

BEGIN TRANSACTION;

UPDATE Reports
SET Status     = 'reviewed',
    ReviewedBy = 6,
    ReviewedAt = strftime('%Y-%m-%dT%H:%M:%SZ', 'now')
WHERE PostID = 21 AND Status = 'open';

UPDATE Posts
SET Content = '[removed by moderator: spam]'
WHERE PostID = 21;

DELETE FROM Post_hashtags WHERE PostID = 21;

--- INSIDE the transaction: queue is empty, post redacted, tags detached ---
SELECT PostID, ReportCount FROM ModerationQueue;
SELECT COUNT(*) AS HashtagLinks FROM Post_hashtags WHERE PostID = 21;
SELECT Content FROM Posts WHERE PostID = 21;

ROLLBACK;   -- change to COMMIT to make the moderation action permanent

--- AFTER ROLLBACK: everything is back exactly as it was ---
SELECT PostID, ReportCount FROM ModerationQueue;
SELECT COUNT(*) AS HashtagLinks FROM Post_hashtags WHERE PostID = 21;
SELECT substr(Content, 1, 40) AS Content FROM Posts WHERE PostID = 21;
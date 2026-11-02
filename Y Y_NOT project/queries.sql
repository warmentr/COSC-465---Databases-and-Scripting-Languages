-- Requirement 1: Filtering and Sorting
-- Shows regular users' posts from the last few days of the dataset (Oct 19 onward), newest first.
-- Moderator/admin announcements are filtered out, like a "recent community activity" page.
SELECT p.PostID,
       u.Username          AS Author,
       p.CreatedAt         AS PostedAt,
       substr(p.Content, 1, 60) AS Preview
FROM Posts p
JOIN Users u ON u.UserID = p.UserID
WHERE p.CreatedAt >= '2026-10-19T00:00:00Z'
  AND u.Role = 'user'
ORDER BY p.CreatedAt DESC;

-- Requirement 2: INNER JOIN
-- Shows each comment together with the username of the person who wrote it,
-- so the comment feed displays names instead of raw UserIDs.
SELECT c.CommentID,
       u.Username  AS Commenter,
       c.PostID    AS OnPostID,
       c.Body      AS Comment,
       c.CreatedAt AS CommentedAt
FROM Comments c
INNER JOIN Users u ON u.UserID = c.UserID
ORDER BY c.PostID, c.CreatedAt;

-- Requirement 3: LEFT JOIN
-- Finds posts that nobody has liked yet. Every post is kept; posts with no matching row in
-- Likes show NULL in MatchingLikeID, so the WHERE ___ IS NULL keeps only the unliked ones.
-- Useful for spotting posts that need attention (note the spam giveaway is in the list).
SELECT p.PostID,
       u.Username  AS Author,
       p.CreatedAt AS PostedAt,
       l.LikeID    AS MatchingLikeID
FROM Posts p
JOIN Users u ON u.UserID = p.UserID
LEFT JOIN Likes l ON l.PostID = p.PostID
WHERE l.LikeID IS NULL
ORDER BY p.CreatedAt DESC;

-- Requirement 4: Three-Table Join (Users, Posts, Post_hashtags, Hashtags)
-- Shows which hashtags each user has posted about, and how many posts they have made with tags.
-- This needs four tables because hashtags are linked to users only through posts.
SELECT u.Username                      AS Username,
       COUNT(DISTINCT p.PostID)        AS TaggedPosts,
       GROUP_CONCAT(DISTINCT h.Tag)    AS HashtagsUsed
FROM Users u
JOIN Posts p          ON p.UserID    = u.UserID
JOIN Post_hashtags ph ON ph.PostID   = p.PostID
JOIN Hashtags h       ON h.HashtagID = ph.HashtagID
GROUP BY u.UserID, u.Username
ORDER BY u.Username;

-- Requirement 5: Aggregate Query
-- Platform-wide post summary: how many posts exist, the date range they cover,
-- and the average post length in characters.
SELECT COUNT(*)                     AS TotalPosts,
       MIN(CreatedAt)               AS FirstPost,
       MAX(CreatedAt)               AS LatestPost,
       ROUND(AVG(LENGTH(Content)),1) AS AvgPostLength
FROM Posts;

-- Requirement 6: GROUP BY and HAVING
-- Lists hashtags used in at least 3 posts (the "popular topics" report).
-- HAVING removes the one- and two-post tags such as #Giveaway and #Crossover.
SELECT h.Tag        AS Hashtag,
       COUNT(*)     AS PostCount
FROM Hashtags h
JOIN Post_hashtags ph ON ph.HashtagID = h.HashtagID
GROUP BY h.HashtagID, h.Tag
HAVING COUNT(*) >= 3
ORDER BY PostCount DESC, h.Tag;

-- Requirement 7: Subquery
-- Finds posts with more likes than the average post (total likes / total posts, about 2.24).
-- The scalar subquery computes that platform average; the correlated subquery counts likes per post.
SELECT p.PostID,
       u.Username AS Author,
       (SELECT COUNT(*) FROM Likes l WHERE l.PostID = p.PostID) AS Likes
FROM Posts p
JOIN Users u ON u.UserID = p.UserID
WHERE (SELECT COUNT(*) FROM Likes l WHERE l.PostID = p.PostID)
    > (SELECT COUNT(*) * 1.0 / (SELECT COUNT(*) FROM Posts) FROM Likes)
ORDER BY Likes DESC, p.PostID;

-- Requirement 8: Set Operation (INTERSECT)
-- Finds mutual followers ("friends"): pairs where A follows B AND B follows A, both accepted.
-- INTERSECT keeps only the follow rows whose reverse also exists. A < B lists each pair once.
SELECT ua.Username AS UserA,
       ub.Username AS UserB
FROM (
    SELECT FollowerID AS A, FolloweeID AS B FROM Follows WHERE Status = 'accepted'
    INTERSECT
    SELECT FolloweeID,      FollowerID      FROM Follows WHERE Status = 'accepted'
) AS mutual
JOIN Users ua ON ua.UserID = mutual.A
JOIN Users ub ON ub.UserID = mutual.B
WHERE mutual.A < mutual.B
ORDER BY ua.Username, ub.Username;

-- Requirement 9: View (FollowingFeed)
-- Home feed for honey_hive_hq (UserID 1): the newest posts from accounts they follow with an
-- accepted request. The view hides a join across Follows, Posts and Users, so the app only
-- needs one filter. Pending requests (ex to private user 4) correctly do not appear.
SELECT AuthorUsername AS Author,
       PostID,
       CreatedAt      AS PostedAt,
       substr(Content, 1, 55) AS Preview
FROM FollowingFeed
WHERE ViewerID = 1
ORDER BY CreatedAt DESC
LIMIT 8;
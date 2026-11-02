DBMS USED: I am using sqlite3 for this project.

Past Deliverables:
In order to setup this use the schema.sql and insert_data.sql as follows:

sqlite3 yynot.db
> .read schema.sql
> .read insert_data.sql

This will create all of the necessary tables and populate them with some synthetic
data I created designed to resemble some movie fan pages. It also creates one admin and moderator.

Views:
There are 6 views currently for this database:
1. TrendingHashtags - shows hashtag usage over the last 7 days in the dataset.
2. ModerationQueue - shows posts with open reports that need to be checked by a moderator. only shows each post ones due to a unique constraint
3. PendingFollowRequests - shows the requests waiting on approval for private accounts.
4. FollowingFeed - contains the posts from people the user follows.
5. UserStats - the view shows profile numbers per user. Only accepted followers count here.
6. PostStats - the view shows each post with its author and like/comment counts

Indexes:
There are 4 indexes in this database:
1. idx_post_user - indexes over the posts table to find the author of the post.
2. idx_comments_post - indexes over the comments table to find the post it was made on.
3. idx_likes_post - indexes over the likes table to find the post that was liked.
4. idx_follows_followee - indexes over the follows table to find who is being followed.

Design Changes:
There have been no significant design chances since the last deliverable.
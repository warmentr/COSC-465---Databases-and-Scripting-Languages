# All SQL for the Y, Y not application lives in this module.

import re
import sqlite3

STAFF_ROLES = ("moderator", "admin")
MAX_POST_LEN = 280
MAX_COMMENT_LEN = 280
MAX_REASON_LEN = 200
HASHTAG_RE = re.compile(r"#(\w+)")
NOW_SQL = "strftime('%Y-%m-%dT%H:%M:%SZ', 'now')"


class AppError(Exception):
    """A user-facing problem (invalid input, not found, duplicate, not allowed)."""


# A post is visible if its author is public, it is the viewer's own, the viewer
# is staff, or the viewer follows the author with an accepted request.
VISIBLE_SQL = """(u.IsPrivate = 0 OR u.UserID = :viewer OR :is_staff = 1
    OR EXISTS (SELECT 1 FROM Follows f
               WHERE f.FollowerID = :viewer AND f.FolloweeID = u.UserID
                 AND f.Status = 'accepted'))"""


def is_staff(user):
    return user["Role"] in STAFF_ROLES


def require_staff(user):
    if not is_staff(user):
        raise AppError("Only moderators and admins can do that.")


def _viewer_params(viewer, **extra):
    return {"viewer": viewer["UserID"], "is_staff": 1 if is_staff(viewer) else 0, **extra}


def _escape_like(text):
    return text.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")


def _require_visible_post(conn, viewer, post_id):
    row = conn.execute(
        """SELECT p.PostID FROM Posts p JOIN Users u ON u.UserID = p.UserID
           WHERE p.PostID = :post_id AND """ + VISIBLE_SQL,
        _viewer_params(viewer, post_id=post_id),
    ).fetchone()
    if row is None:
        raise AppError(f"Post {post_id} was not found.")


# ---------------------------------------------------------------- users

def list_usernames(conn):
    return [r["Username"] for r in conn.execute("SELECT Username FROM Users ORDER BY Username")]


def get_user_by_username(conn, username):
    return conn.execute(
        "SELECT UserID, Username, IsPrivate, Role FROM Users WHERE Username = ? COLLATE NOCASE",
        (username,),
    ).fetchone()


# ------------------------------------------- 1. search / browse posts

def search_posts(conn, viewer, keyword=None, tag=None, author=None, limit=20):
    sql = """
        SELECT ps.PostID, ps.Username AS Author, ps.CreatedAt AS PostedAt,
               ps.LikeCount AS Likes, ps.CommentCount AS Comments,
               substr(ps.Content, 1, 60) AS Preview
        FROM PostStats ps
        JOIN Users u ON u.UserID = ps.UserID
        WHERE """ + VISIBLE_SQL
    params = _viewer_params(viewer, limit=limit)
    if keyword:
        sql += " AND ps.Content LIKE :kw ESCAPE '\\'"
        params["kw"] = "%" + _escape_like(keyword) + "%"
    if tag:
        sql += """ AND EXISTS (SELECT 1 FROM Post_hashtags ph
                               JOIN Hashtags h ON h.HashtagID = ph.HashtagID
                               WHERE ph.PostID = ps.PostID AND h.Tag = :tag COLLATE NOCASE)"""
        params["tag"] = tag
    if author:
        sql += " AND ps.Username = :author COLLATE NOCASE"
        params["author"] = author
    sql += " ORDER BY ps.CreatedAt DESC LIMIT :limit"
    return conn.execute(sql, params).fetchall()


# ------------------------------- 2. related data: post + author + tags + comments

def get_post_details(conn, viewer, post_id):
    post = conn.execute(
        """SELECT ps.PostID, ps.Username AS Author, ps.CreatedAt, ps.Content,
                  ps.LikeCount, ps.CommentCount,
                  EXISTS (SELECT 1 FROM Likes l
                          WHERE l.PostID = ps.PostID AND l.UserID = :viewer) AS LikedByYou
           FROM PostStats ps
           JOIN Users u ON u.UserID = ps.UserID
           WHERE ps.PostID = :post_id AND """ + VISIBLE_SQL,
        _viewer_params(viewer, post_id=post_id),
    ).fetchone()
    if post is None:
        raise AppError(f"Post {post_id} was not found.")
    tags = conn.execute(
        """SELECT h.Tag FROM Post_hashtags ph
           JOIN Hashtags h ON h.HashtagID = ph.HashtagID
           WHERE ph.PostID = ? ORDER BY h.Tag""",
        (post_id,),
    ).fetchall()
    comments = conn.execute(
        """SELECT c.CommentID, u.Username AS Commenter, c.Body, c.CreatedAt
           FROM Comments c JOIN Users u ON u.UserID = c.UserID
           WHERE c.PostID = ? ORDER BY c.CreatedAt""",
        (post_id,),
    ).fetchall()
    return post, [t["Tag"] for t in tags], comments


# ------------------------------------------------------ 3. add data

def extract_hashtags(text):
    """Unique hashtags in order of appearance (case-insensitive), without the #."""
    seen = {}
    for tag in HASHTAG_RE.findall(text):
        seen.setdefault(tag.lower(), tag)
    return list(seen.values())


def create_post(conn, user, content):
    """Insert a post and link its hashtags. One transaction: all or nothing."""
    content = (content or "").strip()
    if not content:
        raise AppError("A post cannot be empty.")
    if len(content) > MAX_POST_LEN:
        raise AppError(f"A post can be at most {MAX_POST_LEN} characters.")
    tags = extract_hashtags(content)
    with conn:  # commits on success, rolls back if anything below raises
        post_id = conn.execute(
            "INSERT INTO Posts (UserID, Content) VALUES (?, ?)", (user["UserID"], content)
        ).lastrowid
        for tag in tags:
            row = conn.execute(
                "SELECT HashtagID FROM Hashtags WHERE Tag = ? COLLATE NOCASE", (tag,)
            ).fetchone()
            if row is None:  # new hashtag
                hashtag_id = conn.execute(
                    "INSERT INTO Hashtags (Tag) VALUES (?)", (tag,)
                ).lastrowid
            else:
                hashtag_id = row["HashtagID"]
            conn.execute(
                "INSERT INTO Post_hashtags (PostID, HashtagID) VALUES (?, ?)",
                (post_id, hashtag_id),
            )
    return post_id, tags


def add_comment(conn, user, post_id, body):
    body = (body or "").strip()
    if not body:
        raise AppError("A comment cannot be empty.")
    if len(body) > MAX_COMMENT_LEN:
        raise AppError(f"A comment can be at most {MAX_COMMENT_LEN} characters.")
    _require_visible_post(conn, user, post_id)
    with conn:
        return conn.execute(
            "INSERT INTO Comments (PostID, UserID, Body) VALUES (?, ?, ?)",
            (post_id, user["UserID"], body),
        ).lastrowid


def like_post(conn, user, post_id):
    _require_visible_post(conn, user, post_id)
    try:
        with conn:
            conn.execute("INSERT INTO Likes (UserID, PostID) VALUES (?, ?)",
                         (user["UserID"], post_id))
    except sqlite3.IntegrityError:  # UNIQUE (UserID, PostID)
        raise AppError("You already liked that post.") from None


def report_post(conn, user, post_id, reason):
    reason = (reason or "").strip()
    if not reason:
        raise AppError("A reason is required.")
    if len(reason) > MAX_REASON_LEN:
        raise AppError(f"The reason can be at most {MAX_REASON_LEN} characters.")
    _require_visible_post(conn, user, post_id)
    try:
        with conn:
            conn.execute(
                "INSERT INTO Reports (PostID, ReporterID, Reason) VALUES (?, ?, ?)",
                (post_id, user["UserID"], reason),
            )
    except sqlite3.IntegrityError:  # UNIQUE (ReporterID, PostID)
        raise AppError("You have already reported that post.") from None


# ------------------------------------------- 4. update / delete data

def unlike_post(conn, user, post_id):
    with conn:
        cur = conn.execute("DELETE FROM Likes WHERE UserID = ? AND PostID = ?",
                           (user["UserID"], post_id))
    if cur.rowcount == 0:
        raise AppError("You have not liked that post.")


def pending_requests(conn, user):
    return conn.execute(
        """SELECT FollowerID, RequesterUsername AS Requester, CreatedAt
           FROM PendingFollowRequests WHERE FolloweeID = ? ORDER BY CreatedAt""",
        (user["UserID"],),
    ).fetchall()


def respond_to_follow_request(conn, user, follower_id, accept):
    """Accept (UPDATE) or decline (DELETE) a pending follow request sent to `user`."""
    with conn:
        if accept:
            cur = conn.execute(
                """UPDATE Follows SET Status = 'accepted'
                   WHERE FolloweeID = ? AND FollowerID = ? AND Status = 'pending'""",
                (user["UserID"], follower_id),
            )
        else:
            cur = conn.execute(
                """DELETE FROM Follows
                   WHERE FolloweeID = ? AND FollowerID = ? AND Status = 'pending'""",
                (user["UserID"], follower_id),
            )
    if cur.rowcount == 0:
        raise AppError("There is no pending request from that user ID.")


def moderation_queue(conn, mod):
    require_staff(mod)
    return conn.execute(
        """SELECT PostID, AuthorUsername AS Author, ReportCount AS Reports,
                  FirstReportedAt, substr(Content, 1, 50) AS Preview
           FROM ModerationQueue ORDER BY ReportCount DESC, FirstReportedAt"""
    ).fetchall()


def open_reports_for_post(conn, mod, post_id):
    require_staff(mod)
    rows = conn.execute(
        """SELECT r.ReportID, u.Username AS Reporter, r.Reason, r.CreatedAt
           FROM Reports r JOIN Users u ON u.UserID = r.ReporterID
           WHERE r.PostID = ? AND r.Status = 'open' ORDER BY r.CreatedAt""",
        (post_id,),
    ).fetchall()
    if not rows:
        raise AppError(f"Post {post_id} has no open reports.")
    return rows


def dismiss_reports(conn, mod, post_id):
    require_staff(mod)
    with conn:
        cur = conn.execute(
            f"""UPDATE Reports SET Status = 'dismissed', ReviewedBy = ?, ReviewedAt = {NOW_SQL}
                WHERE PostID = ? AND Status = 'open'""",
            (mod["UserID"], post_id),
        )
    if cur.rowcount == 0:
        raise AppError(f"Post {post_id} has no open reports.")
    return cur.rowcount


def remove_post(conn, mod, post_id):
    """Moderator removes a reported post (the Deliverable 4 transaction).

    Three changes that must succeed or fail together: close the open reports,
    replace the post text with a notice, and detach its hashtags.
    """
    require_staff(mod)
    with conn:
        cur = conn.execute(
            f"""UPDATE Reports SET Status = 'reviewed', ReviewedBy = ?, ReviewedAt = {NOW_SQL}
                WHERE PostID = ? AND Status = 'open'""",
            (mod["UserID"], post_id),
        )
        if cur.rowcount == 0:
            raise AppError(f"Post {post_id} has no open reports.")  # triggers rollback
        conn.execute("UPDATE Posts SET Content = ? WHERE PostID = ?",
                     ("[removed by moderator]", post_id))
        conn.execute("DELETE FROM Post_hashtags WHERE PostID = ?", (post_id,))
    return cur.rowcount


# --------------------------------------- 5. summaries and reports

def platform_summary(conn):
    return conn.execute(
        """SELECT (SELECT COUNT(*) FROM Users)    AS Users,
                  (SELECT COUNT(*) FROM Posts)    AS Posts,
                  (SELECT COUNT(*) FROM Comments) AS Comments,
                  (SELECT COUNT(*) FROM Likes)    AS Likes,
                  (SELECT COUNT(*) FROM Reports WHERE Status = 'open') AS OpenReports,
                  (SELECT MIN(CreatedAt) FROM Posts) AS FirstPost,
                  (SELECT MAX(CreatedAt) FROM Posts) AS LatestPost,
                  (SELECT ROUND(AVG(LENGTH(Content)), 1) FROM Posts) AS AvgPostLength"""
    ).fetchone()


def popular_hashtags(conn, min_posts):
    return conn.execute(
        """SELECT h.Tag AS Hashtag, COUNT(*) AS PostCount
           FROM Hashtags h JOIN Post_hashtags ph ON ph.HashtagID = h.HashtagID
           GROUP BY h.HashtagID, h.Tag
           HAVING COUNT(*) >= ?
           ORDER BY PostCount DESC, h.Tag""",
        (min_posts,),
    ).fetchall()


def user_leaderboard(conn):
    return conn.execute(
        """SELECT us.Username, us.PostCount AS Posts, us.FollowerCount AS Followers,
                  us.FollowingCount AS Following,
                  COALESCE(SUM(ps.LikeCount), 0) AS LikesReceived
           FROM UserStats us
           LEFT JOIN PostStats ps ON ps.UserID = us.UserID
           GROUP BY us.UserID, us.Username, us.PostCount, us.FollowerCount, us.FollowingCount
           ORDER BY LikesReceived DESC, us.Username"""
    ).fetchall()


# ------------------------------- 6. additional: home feed and following

def home_feed(conn, user, limit=10):
    return conn.execute(
        """SELECT PostID, AuthorUsername AS Author, CreatedAt AS PostedAt,
                  substr(Content, 1, 60) AS Preview
           FROM FollowingFeed WHERE ViewerID = ?
           ORDER BY CreatedAt DESC LIMIT ?""",
        (user["UserID"], limit),
    ).fetchall()


def follow_user(conn, user, username):
    """Follow someone: public accounts accept immediately, private ones stay pending."""
    target = get_user_by_username(conn, username)
    if target is None:
        raise AppError(f"No user named '{username}'.")
    if target["UserID"] == user["UserID"]:
        raise AppError("You cannot follow yourself.")
    status = "pending" if target["IsPrivate"] else "accepted"
    try:
        with conn:
            conn.execute(
                "INSERT INTO Follows (FollowerID, FolloweeID, Status) VALUES (?, ?, ?)",
                (user["UserID"], target["UserID"], status),
            )
    except sqlite3.IntegrityError:  # primary key (FollowerID, FolloweeID)
        raise AppError(f"You already follow {target['Username']} or have a pending request.") from None
    return target["Username"], status


def unfollow_user(conn, user, username):
    target = get_user_by_username(conn, username)
    if target is None:
        raise AppError(f"No user named '{username}'.")
    with conn:
        cur = conn.execute("DELETE FROM Follows WHERE FollowerID = ? AND FolloweeID = ?",
                           (user["UserID"], target["UserID"]))
    if cur.rowcount == 0:
        raise AppError(f"You are not following {target['Username']}.")
    return target["Username"]
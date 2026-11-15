#!/usr/bin/env python3
import os
import sqlite3
import sys

import db
import operations as ops
import ui
from operations import AppError


class Session:
    """Holds the currently logged-in user (a row from the Users table)."""

    def __init__(self):
        self.user = None


# ---------------------------------------------------------------- login

def log_in(conn, session):
    print("Available users: " + ", ".join(ops.list_usernames(conn)))
    while True:
        name = ui.ask_text("Log in as (username, blank to cancel): ")
        if name is None:
            return False
        user = ops.get_user_by_username(conn, name)
        if user is None:
            print("  No such user.")
            continue
        session.user = user
        print(f"Logged in as {user['Username']} ({user['Role']}).")
        return True


# ------------------------------------------------------------- handlers

def browse_posts(conn, session):
    print("Leave a filter blank to skip it (all blank = newest 20 posts).")
    keyword = ui.ask_text("  Text contains: ")
    tag = ui.ask_text("  Hashtag (without #): ")
    author = ui.ask_text("  Author username: ")
    rows = ops.search_posts(conn, session.user, keyword, (tag or "").lstrip("#") or None, author)
    ui.print_table(rows, "No matching posts.")


def view_post(conn, session):
    post_id = ui.ask_int("Post ID: ", minimum=1)
    if post_id is None:
        return
    post, tags, comments = ops.get_post_details(conn, session.user, post_id)
    print(f"\nPost #{post['PostID']} by {post['Author']} on {post['CreatedAt']}")
    ui.print_wrapped(post["Content"])
    print(f"  Hashtags: {', '.join('#' + t for t in tags) if tags else '(none)'}")
    liked = " (you liked it)" if post["LikedByYou"] else ""
    print(f"  Likes: {post['LikeCount']}{liked}   Comments: {post['CommentCount']}")
    if comments:
        print("\nComments:")
        ui.print_table(comments)


def create_post(conn, session):
    print(f"Write your post (max {ops.MAX_POST_LEN} characters). Use #hashtags inline.")
    content = ui.ask_text("> ", max_len=ops.MAX_POST_LEN)
    if content is None:
        return
    post_id, tags = ops.create_post(conn, session.user, content)
    extra = f" Hashtags: {', '.join('#' + t for t in tags)}." if tags else ""
    print(f"Post #{post_id} created.{extra}")


def comment_on_post(conn, session):
    post_id = ui.ask_int("Post ID to comment on: ", minimum=1)
    if post_id is None:
        return
    body = ui.ask_text("Comment: ", max_len=ops.MAX_COMMENT_LEN)
    if body is None:
        return
    comment_id = ops.add_comment(conn, session.user, post_id, body)
    print(f"Comment #{comment_id} added.")


def like_or_unlike(conn, session):
    post_id = ui.ask_int("Post ID: ", minimum=1)
    if post_id is None:
        return
    action = ui.ask_choice("[l]ike or [u]nlike: ", {"l", "u"})
    if action == "l":
        ops.like_post(conn, session.user, post_id)
        print("Post liked.")
    elif action == "u":
        ops.unlike_post(conn, session.user, post_id)
        print("Like removed.")


def report_post(conn, session):
    post_id = ui.ask_int("Post ID to report: ", minimum=1)
    if post_id is None:
        return
    reason = ui.ask_text("Reason: ", max_len=ops.MAX_REASON_LEN)
    if reason is None:
        return
    ops.report_post(conn, session.user, post_id, reason)
    print("Report submitted. Thank you.")


def home_feed(conn, session):
    print(f"Newest posts from people {session.user['Username']} follows:")
    ui.print_table(ops.home_feed(conn, session.user),
                   "Nothing here yet. Follow some users first!")


def follow_menu(conn, session):
    action = ui.ask_choice("[f]ollow or [u]nfollow a user: ", {"f", "u"})
    if action is None:
        return
    username = ui.ask_text("Username: ")
    if username is None:
        return
    if action == "f":
        name, status = ops.follow_user(conn, session.user, username)
        if status == "pending":
            print(f"{name} is private, so your request is pending their approval.")
        else:
            print(f"You now follow {name}.")
    else:
        print(f"You no longer follow {ops.unfollow_user(conn, session.user, username)}.")


def follow_requests(conn, session):
    rows = ops.pending_requests(conn, session.user)
    ui.print_table(rows, "You have no pending follow requests.")
    if not rows:
        return
    follower_id = ui.ask_int("User ID to respond to (blank to go back): ", minimum=1)
    if follower_id is None:
        return
    action = ui.ask_choice("[a]ccept or [d]ecline: ", {"a", "d"})
    if action is None:
        return
    ops.respond_to_follow_request(conn, session.user, follower_id, action == "a")
    print("Request accepted." if action == "a" else "Request declined.")


def moderate(conn, session):
    queue = ops.moderation_queue(conn, session.user)  # raises AppError for non-staff
    ui.print_table(queue, "The moderation queue is empty.")
    if not queue:
        return
    post_id = ui.ask_int("Post ID to review (blank to go back): ", minimum=1)
    if post_id is None:
        return
    ui.print_table(ops.open_reports_for_post(conn, session.user, post_id))
    action = ui.ask_choice("[d]ismiss reports, [r]emove post, [c]ancel: ", {"d", "r", "c"})
    if action == "d":
        count = ops.dismiss_reports(conn, session.user, post_id)
        print(f"{count} report(s) dismissed. The post stays up.")
    elif action == "r":
        if ui.confirm("Remove this post's content and hashtags?"):
            count = ops.remove_post(conn, session.user, post_id)
            print(f"Post removed and {count} report(s) marked reviewed.")
        else:
            print("Cancelled.")


def reports_menu(conn, session):
    print("  1) Platform summary\n  2) Popular hashtags\n  3) User leaderboard")
    choice = ui.ask_int("Choose a report: ", minimum=1, maximum=3)
    if choice == 1:
        ui.print_record(ops.platform_summary(conn))
    elif choice == 2:
        n = ui.ask_int("Minimum number of posts per hashtag [default 3]: ", minimum=1)
        ui.print_table(ops.popular_hashtags(conn, n or 3), "No hashtags meet that threshold.")
    elif choice == 3:
        ui.print_table(ops.user_leaderboard(conn))


def switch_user(conn, session):
    log_in(conn, session)


# (label, handler). The menu number is the position in this list (1-based).
MENU = [
    ("Browse / search posts", browse_posts),
    ("View a post with its hashtags and comments", view_post),
    ("Create a post", create_post),
    ("Comment on a post", comment_on_post),
    ("Like / unlike a post", like_or_unlike),
    ("Report a post", report_post),
    ("My home feed (posts from people I follow)", home_feed),
    ("Follow / unfollow a user", follow_menu),
    ("Review my pending follow requests", follow_requests),
    ("Moderation queue (moderators/admins only)", moderate),
    ("Reports and statistics", reports_menu),
    ("Switch user", switch_user),
]


def print_menu(session):
    print(f"\n=== Y, Y not  |  logged in as {session.user['Username']} ({session.user['Role']}) ===")
    for number, (label, _) in enumerate(MENU, start=1):
        print(f"  {number:>2}) {label}")
    print("   0) Quit")


def main():
    path = sys.argv[1] if len(sys.argv) > 1 else None
    try:
        conn = db.get_connection(path)
    except db.DatabaseNotFound as err:
        print(err)
        return 1
    except sqlite3.Error:
        print("Could not open the database file.")
        return 1

    session = Session()
    try:
        if not log_in(conn, session):
            return 0
        while True:
            print_menu(session)
            choice = ui.ask_int("Choose an option: ", minimum=0, maximum=len(MENU))
            if choice is None:
                continue
            if choice == 0:
                break
            _, handler = MENU[choice - 1]
            try:
                handler(conn, session)
            except AppError as err:
                print(f"Cannot do that: {err}")
            except sqlite3.Error as err:
                print("Database error: the operation could not be completed. No changes were saved.")
                if os.environ.get("YYNOT_DEBUG"):
                    print(f"  (debug) {err}")
    except (EOFError, KeyboardInterrupt):
        print()
    finally:
        conn.close()
    print("Goodbye!")
    return 0


if __name__ == "__main__":
    sys.exit(main())
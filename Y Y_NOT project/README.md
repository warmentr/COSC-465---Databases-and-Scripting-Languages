# Y, Y not - Deliverable 5: Application

**Language:** Python 3.8+ (tested on 3.13). **DBMS:** SQLite 3.
**Packages:** none beyond the standard library (`sqlite3`), so there is nothing to install.

## Files
- `app.py` - menu and user interaction (run this)
- `operations.py` - all SQL (parameterized) and business rules
- `db.py` - database connection (turns on `PRAGMA foreign_keys`)
- `ui.py` - input validation and table printing
- `schema.sql`, `insert_data.sql` - unchanged from earlier deliverables (no schema changes)

## Setup
1. Put all files in one folder and create the database:
   ```
   sqlite3 yynot.db < schema.sql
   sqlite3 yynot.db < insert_data.sql
   ```
   (Or `sqlite3 yynot.db` then `.read schema.sql` and `.read insert_data.sql`.)
2. Database connection: the app opens `yynot.db` in the same folder as `app.py`.
   To use another file, pass it as an argument (`python3 app.py path/to/other.db`).
   No credentials are needed.
3. Start the app:
   ```
   python3 app.py
   ```
4. Log in by typing a username (no password). Good ones to try:
   - `honey_hive_hq` - regular user (has an open spam post and pending follow requests out)
   - `mod_mira` - moderator (can use the moderation queue)
   - `spice_must_flow` - private account with 2 pending follow requests to approve
   Use menu option 12 to switch users. Press Enter at most prompts to cancel.

Set `YYNOT_DEBUG=1` to also show raw database error details (off by default).

## The six required operations
| # | Category | Menu option | What it does |
|---|----------|-------------|--------------|
| 1 | Search / browse | **1** Browse / search posts | Filter by text, hashtag and/or author; newest first |
| 2 | Related data (join) | **2** View a post | Post + author + hashtags + comments with commenter names (joins across Posts, Users, Post_hashtags, Hashtags, Comments) |
| 3 | Add data (INSERT) | **3** Create a post (also 4 comment, 5 like, 6 report, 8 follow) | Inserts the post and its hashtags in one transaction |
| 4 | Update / delete | **10** Moderation queue (also 9 follow requests, 5 unlike, 8 unfollow) | Moderator dismisses reports (UPDATE) or removes a post (3 changes in one transaction); users accept (UPDATE) or decline (DELETE) follow requests |
| 5 | Summary / report | **11** Reports and statistics | Platform summary (aggregates), popular hashtags (GROUP BY/HAVING), user leaderboard (view + join + GROUP BY) |
| 6 | Additional | **7** My home feed (and 8 follow/unfollow) | Posts from followed users via the `FollowingFeed` view; private accounts make follows pending |

## Notes
- Validation: IDs must be whole numbers >= 1, text is required and length-limited (posts/comments 280 chars, report reason 200), menu choices are range-checked.
- Errors: not-found, duplicate (already liked / reported / following), self-follow, and permission problems show a clear message; unexpected database errors show a generic message and nothing is saved.
- Private accounts' posts are only visible to accepted followers (and staff).
- The database is the only data store; the app keeps just the logged-in user's row in memory.
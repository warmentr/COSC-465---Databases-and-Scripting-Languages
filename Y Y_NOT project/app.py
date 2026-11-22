#!/usr/bin/env python3
"""
Y, Y not -- single-file Flask frontend for the yynot.db SQLite database.

Setup:   pip install flask
Run:     python app.py          then open http://127.0.0.1:5000

Put this file in the same folder as yynot.db (or schema.sql + insert_data.sql,
in which case the database is created automatically on first run).

There are no passwords in the schema, so "sign in" is just a user picker in the
top bar -- handy for demoing regular users, a private account, a moderator and
an admin.
"""
import os
import re
import sqlite3
from datetime import datetime, timezone
from functools import wraps

from flask import (Flask, flash, g, redirect, render_template, request,
                   session, url_for, abort)
from jinja2 import DictLoader
from markupsafe import Markup, escape

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, "yynot.db")
MAX_POST = 500
MAX_COMMENT = 300

app = Flask(__name__)
app.secret_key = "yynot-demo-secret-change-me"  # only signs the session cookie


# --------------------------------------------------------------------------- #
# Database helpers
# --------------------------------------------------------------------------- #
def init_db_if_missing():
    """Build yynot.db from schema.sql + insert_data.sql if it does not exist."""
    if os.path.exists(DB_PATH):
        return
    schema = os.path.join(BASE_DIR, "schema.sql")
    data = os.path.join(BASE_DIR, "insert_data.sql")
    if not (os.path.exists(schema) and os.path.exists(data)):
        raise SystemExit("yynot.db not found, and schema.sql / insert_data.sql "
                         "are not next to app.py to create it.")
    con = sqlite3.connect(DB_PATH)
    for path in (schema, data):
        with open(path, encoding="utf-8") as f:
            con.executescript(f.read())
    con.close()


def db():
    if "db" not in g:
        g.db = sqlite3.connect(DB_PATH)
        g.db.row_factory = sqlite3.Row
        g.db.execute("PRAGMA foreign_keys = ON")
    return g.db


@app.teardown_appcontext
def close_db(_exc):
    con = g.pop("db", None)
    if con is not None:
        con.close()


def now_iso():
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def q(sql, params=()):
    return db().execute(sql, params).fetchall()


def q1(sql, params=()):
    return db().execute(sql, params).fetchone()


# --------------------------------------------------------------------------- #
# Current user / permissions
# --------------------------------------------------------------------------- #
def current_user():
    if "user" not in g:
        uid = session.get("uid")
        g.user = q1("SELECT * FROM Users WHERE UserID = ?", (uid,)) if uid else None
    return g.user


def is_staff():
    u = current_user()
    return bool(u and u["Role"] in ("moderator", "admin"))


def login_required(fn):
    @wraps(fn)
    def wrapper(*a, **kw):
        if not current_user():
            flash("Pick a user from the top bar first.", "error")
            return redirect(request.referrer or url_for("index"))
        return fn(*a, **kw)
    return wrapper


def staff_required(fn):
    @wraps(fn)
    def wrapper(*a, **kw):
        if not is_staff():
            abort(403)
        return fn(*a, **kw)
    return wrapper


def back():
    return redirect(request.referrer or url_for("index"))


def can_see_user_posts(author_id, author_private):
    """Public accounts: everyone. Private: owner, accepted followers, staff."""
    me = current_user()
    if not author_private or is_staff():
        return True
    if not me:
        return False
    if me["UserID"] == author_id:
        return True
    return q1("SELECT 1 FROM Follows WHERE FollowerID=? AND FolloweeID=? "
              "AND Status='accepted'", (me["UserID"], author_id)) is not None


# --------------------------------------------------------------------------- #
# Post fetching (uses the PostStats view)
# --------------------------------------------------------------------------- #
VISIBLE = """
    (u.IsPrivate = 0
     OR ps.UserID = :me
     OR :staff = 1
     OR EXISTS (SELECT 1 FROM Follows f WHERE f.FollowerID = :me
                AND f.FolloweeID = ps.UserID AND f.Status = 'accepted'))
"""


def fetch_posts(where="1=1", params=None, limit=100):
    me = current_user()
    p = {"me": me["UserID"] if me else -1, "staff": 1 if is_staff() else 0}
    p.update(params or {})
    rows = q(f"""
        SELECT ps.*, u.IsPrivate, u.Role,
               EXISTS (SELECT 1 FROM Likes l
                       WHERE l.PostID = ps.PostID AND l.UserID = :me) AS LikedByMe
        FROM PostStats ps
        JOIN Users u ON u.UserID = ps.UserID
        WHERE {VISIBLE} AND ({where})
        ORDER BY ps.CreatedAt DESC
        LIMIT {int(limit)}""", p)
    posts = [dict(r) for r in rows]
    if posts:
        ids = ",".join(str(x["PostID"]) for x in posts)
        tags = {}
        for r in q(f"""SELECT ph.PostID, h.Tag FROM Post_hashtags ph
                       JOIN Hashtags h ON h.HashtagID = ph.HashtagID
                       WHERE ph.PostID IN ({ids}) ORDER BY h.Tag"""):
            tags.setdefault(r["PostID"], []).append(r["Tag"])
        for post in posts:
            post["Tags"] = tags.get(post["PostID"], [])
    return posts


# --------------------------------------------------------------------------- #
# Template helpers
# --------------------------------------------------------------------------- #
HASHTAG_RE = re.compile(r"(?<![&\w])#(\w+)")


@app.template_filter("linkify")
def linkify(text):
    """Escape the post text, then turn #hashtags into links."""
    safe = str(escape(text))
    out = HASHTAG_RE.sub(
        lambda m: f'<a class="tag" href="{url_for("tag_page", tag=m.group(1))}">#{m.group(1)}</a>',
        safe)
    return Markup(out)


@app.template_filter("when")
def when(iso):
    try:
        return datetime.strptime(iso, "%Y-%m-%dT%H:%M:%SZ").strftime("%b %d, %Y %H:%M UTC")
    except (TypeError, ValueError):
        return iso


@app.context_processor
def inject_globals():
    trending = q("""
        SELECT h.Tag, COUNT(*) AS n
        FROM Hashtags h
        JOIN Post_hashtags ph ON ph.HashtagID = h.HashtagID
        JOIN Posts p ON p.PostID = ph.PostID
        WHERE p.CreatedAt >= strftime('%Y-%m-%dT%H:%M:%SZ',
                                      (SELECT MAX(CreatedAt) FROM Posts), '-7 days')
        GROUP BY h.HashtagID, h.Tag
        ORDER BY n DESC, h.Tag LIMIT 8""")
    open_reports = 0
    if is_staff():
        open_reports = q1("SELECT COUNT(*) AS n FROM ModerationQueue")["n"]
    return dict(me=current_user(), all_users=q("SELECT UserID, Username, Role FROM Users ORDER BY UserID"),
                trending=trending, staff=is_staff(), open_reports=open_reports,
                max_post=MAX_POST, max_comment=MAX_COMMENT)


# --------------------------------------------------------------------------- #
# Routes: session
# --------------------------------------------------------------------------- #
@app.post("/login")
def login():
    uid = request.form.get("uid", "")
    if uid == "":
        session.pop("uid", None)
    elif q1("SELECT 1 FROM Users WHERE UserID = ?", (uid,)):
        session["uid"] = int(uid)
    return back()


# --------------------------------------------------------------------------- #
# Routes: feed, posting, post detail
# --------------------------------------------------------------------------- #
@app.get("/")
def index():
    me = current_user()
    mode = request.args.get("feed", "all")
    if mode == "following" and me:
        # Uses the FollowingFeed view: posts from accepted follows of the viewer.
        posts = fetch_posts("ps.PostID IN (SELECT PostID FROM FollowingFeed WHERE ViewerID = :v)",
                            {"v": me["UserID"]})
    else:
        mode = "all"
        posts = fetch_posts()
    return render_template("index.html", posts=posts, mode=mode)


@app.post("/post")
@login_required
def create_post():
    content = request.form.get("content", "").strip()
    if not content:
        flash("Post can't be empty.", "error")
        return back()
    if len(content) > MAX_POST:
        flash(f"Posts are limited to {MAX_POST} characters.", "error")
        return back()
    con = db()
    try:
        cur = con.execute("INSERT INTO Posts (UserID, Content, CreatedAt) VALUES (?, ?, ?)",
                          (current_user()["UserID"], content, now_iso()))
        post_id = cur.lastrowid
        for tag in dict.fromkeys(HASHTAG_RE.findall(content)):  # unique, ordered
            row = con.execute("SELECT HashtagID FROM Hashtags WHERE Tag = ? COLLATE NOCASE",
                              (tag,)).fetchone()
            if row:
                hid = row["HashtagID"]
            else:
                hid = con.execute("INSERT INTO Hashtags (Tag) VALUES (?)", (tag,)).lastrowid
            con.execute("INSERT OR IGNORE INTO Post_hashtags (PostID, HashtagID) VALUES (?, ?)",
                        (post_id, hid))
        con.commit()
        flash("Posted!", "ok")
    except sqlite3.Error as e:
        con.rollback()
        flash(f"Could not save post: {e}", "error")
    return redirect(url_for("index"))


@app.get("/post/<int:post_id>")
def post_detail(post_id):
    posts = fetch_posts("ps.PostID = :pid", {"pid": post_id}, limit=1)
    if not posts:
        abort(404)
    comments = q("""SELECT c.*, u.Username FROM Comments c
                    JOIN Users u ON u.UserID = c.UserID
                    WHERE c.PostID = ? ORDER BY c.CreatedAt""", (post_id,))
    return render_template("post.html", post=posts[0], comments=comments)


@app.post("/post/<int:post_id>/like")
@login_required
def toggle_like(post_id):
    uid = current_user()["UserID"]
    if not fetch_posts("ps.PostID = :pid", {"pid": post_id}, limit=1):
        abort(404)
    con = db()
    existing = con.execute("SELECT LikeID FROM Likes WHERE UserID=? AND PostID=?",
                           (uid, post_id)).fetchone()
    if existing:
        con.execute("DELETE FROM Likes WHERE LikeID = ?", (existing["LikeID"],))
    else:
        con.execute("INSERT INTO Likes (UserID, PostID, CreatedAt) VALUES (?, ?, ?)",
                    (uid, post_id, now_iso()))
    con.commit()
    return back()


@app.post("/post/<int:post_id>/comment")
@login_required
def add_comment(post_id):
    body = request.form.get("body", "").strip()
    if not fetch_posts("ps.PostID = :pid", {"pid": post_id}, limit=1):
        abort(404)
    if not body or len(body) > MAX_COMMENT:
        flash(f"Comments must be 1-{MAX_COMMENT} characters.", "error")
        return back()
    db().execute("INSERT INTO Comments (PostID, UserID, Body, CreatedAt) VALUES (?, ?, ?, ?)",
                 (post_id, current_user()["UserID"], body, now_iso()))
    db().commit()
    return redirect(url_for("post_detail", post_id=post_id) + "#comments")


@app.post("/post/<int:post_id>/report")
@login_required
def report_post(post_id):
    reason = request.form.get("reason", "").strip()
    posts = fetch_posts("ps.PostID = :pid", {"pid": post_id}, limit=1)
    if not posts:
        abort(404)
    if posts[0]["UserID"] == current_user()["UserID"]:
        flash("You can't report your own post.", "error")
        return back()
    if not reason:
        flash("Please give a reason for the report.", "error")
        return back()
    try:
        db().execute("INSERT INTO Reports (PostID, ReporterID, Reason, CreatedAt) "
                     "VALUES (?, ?, ?, ?)",
                     (post_id, current_user()["UserID"], reason[:200], now_iso()))
        db().commit()
        flash("Report sent to the moderators.", "ok")
    except sqlite3.IntegrityError:   # UNIQUE (ReporterID, PostID)
        db().rollback()
        flash("You've already reported that post.", "error")
    return back()


# --------------------------------------------------------------------------- #
# Routes: hashtags, profiles, follows
# --------------------------------------------------------------------------- #
@app.get("/tag/<tag>")
def tag_page(tag):
    row = q1("SELECT HashtagID, Tag FROM Hashtags WHERE Tag = ? COLLATE NOCASE", (tag,))
    if not row:
        return render_template("tag.html", tag=tag, posts=[])
    posts = fetch_posts("ps.PostID IN (SELECT PostID FROM Post_hashtags WHERE HashtagID = :h)",
                        {"h": row["HashtagID"]})
    return render_template("tag.html", tag=row["Tag"], posts=posts)


@app.get("/user/<username>")
def profile(username):
    user = q1("SELECT * FROM Users WHERE Username = ?", (username,))
    if not user:
        abort(404)
    stats = q1("SELECT * FROM UserStats WHERE UserID = ?", (user["UserID"],))
    me = current_user()
    follow = None
    if me and me["UserID"] != user["UserID"]:
        follow = q1("SELECT Status FROM Follows WHERE FollowerID=? AND FolloweeID=?",
                    (me["UserID"], user["UserID"]))
    visible = can_see_user_posts(user["UserID"], user["IsPrivate"])
    posts = fetch_posts("ps.UserID = :a", {"a": user["UserID"]}) if visible else []
    requests_in = []
    if me and me["UserID"] == user["UserID"]:
        requests_in = q("SELECT * FROM PendingFollowRequests WHERE FolloweeID = ? "
                        "ORDER BY CreatedAt", (me["UserID"],))
    return render_template("profile.html", user=user, stats=stats, follow=follow,
                           visible=visible, posts=posts, requests_in=requests_in)


@app.post("/follow/<int:user_id>")
@login_required
def toggle_follow(user_id):
    me = current_user()["UserID"]
    target = q1("SELECT * FROM Users WHERE UserID = ?", (user_id,))
    if not target:
        abort(404)
    if target["UserID"] == me:
        flash("You can't follow yourself.", "error")
        return back()
    existing = q1("SELECT Status FROM Follows WHERE FollowerID=? AND FolloweeID=?", (me, user_id))
    if existing:
        db().execute("DELETE FROM Follows WHERE FollowerID=? AND FolloweeID=?", (me, user_id))
        flash("Unfollowed." if existing["Status"] == "accepted" else "Request cancelled.", "ok")
    else:
        status = "pending" if target["IsPrivate"] else "accepted"
        db().execute("INSERT INTO Follows (FollowerID, FolloweeID, Status, CreatedAt) "
                     "VALUES (?, ?, ?, ?)", (me, user_id, status, now_iso()))
        flash("Follow request sent." if status == "pending" else "Following!", "ok")
    db().commit()
    return back()


@app.post("/follow-request/<int:follower_id>")
@login_required
def respond_follow_request(follower_id):
    me = current_user()["UserID"]
    if request.form.get("action") == "accept":
        db().execute("UPDATE Follows SET Status='accepted' WHERE FollowerID=? AND FolloweeID=? "
                     "AND Status='pending'", (follower_id, me))
        flash("Request accepted.", "ok")
    else:
        db().execute("DELETE FROM Follows WHERE FollowerID=? AND FolloweeID=? AND Status='pending'",
                     (follower_id, me))
        flash("Request declined.", "ok")
    db().commit()
    return back()


# --------------------------------------------------------------------------- #
# Routes: moderation (moderator / admin only)
# --------------------------------------------------------------------------- #
@app.get("/mod")
@staff_required
def moderation():
    queue = [dict(r) for r in q("SELECT * FROM ModerationQueue ORDER BY ReportCount DESC, "
                                "LastReportedAt DESC")]
    for item in queue:
        item["Reports"] = q("""SELECT r.Reason, r.CreatedAt, u.Username AS Reporter
                               FROM Reports r JOIN Users u ON u.UserID = r.ReporterID
                               WHERE r.PostID = ? AND r.Status = 'open'
                               ORDER BY r.CreatedAt""", (item["PostID"],))
    history = q("""SELECT r.ReportID, r.PostID, r.Reason, r.Status, r.ReviewedAt,
                          rp.Username AS Reporter, rv.Username AS Reviewer
                   FROM Reports r
                   JOIN Users rp ON rp.UserID = r.ReporterID
                   LEFT JOIN Users rv ON rv.UserID = r.ReviewedBy
                   WHERE r.Status <> 'open' ORDER BY r.ReviewedAt DESC""")
    return render_template("mod.html", queue=queue, history=history)


@app.post("/mod/remove/<int:post_id>")
@staff_required
def mod_remove(post_id):
    """Same three-step transaction as transaction.sql, but committed."""
    con = db()
    try:
        con.execute("""UPDATE Reports SET Status='reviewed', ReviewedBy=?, ReviewedAt=?
                       WHERE PostID=? AND Status='open'""",
                    (current_user()["UserID"], now_iso(), post_id))
        con.execute("UPDATE Posts SET Content='[removed by moderator]' WHERE PostID=?", (post_id,))
        con.execute("DELETE FROM Post_hashtags WHERE PostID=?", (post_id,))
        con.commit()
        flash(f"Post #{post_id} removed and its reports marked reviewed.", "ok")
    except sqlite3.Error as e:
        con.rollback()
        flash(f"Removal failed, nothing was changed: {e}", "error")
    return redirect(url_for("moderation"))


@app.post("/mod/dismiss/<int:post_id>")
@staff_required
def mod_dismiss(post_id):
    db().execute("""UPDATE Reports SET Status='dismissed', ReviewedBy=?, ReviewedAt=?
                    WHERE PostID=? AND Status='open'""",
                 (current_user()["UserID"], now_iso(), post_id))
    db().commit()
    flash(f"Reports on post #{post_id} dismissed.", "ok")
    return redirect(url_for("moderation"))


# --------------------------------------------------------------------------- #
# Error pages
# --------------------------------------------------------------------------- #
@app.errorhandler(403)
def forbidden(_e):
    return render_template("error.html", code=403, msg="Moderators and admins only."), 403


@app.errorhandler(404)
def not_found(_e):
    return render_template("error.html", code=404, msg="That page doesn't exist (or you can't see it)."), 404


# --------------------------------------------------------------------------- #
# Templates (kept inline so the whole frontend is this one file)
# --------------------------------------------------------------------------- #
TEMPLATES = {}

TEMPLATES["base.html"] = r"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{% block title %}Y, Y not{% endblock %}</title>
<style>
  :root { --bg:#faf7f0; --card:#fff; --ink:#1f2328; --muted:#6b7280; --line:#e7e1d2;
          --accent:#d98e04; --accent-d:#b57400; --danger:#b42318; --ok:#1a7f37; }
  * { box-sizing: border-box; }
  body { margin:0; background:var(--bg); color:var(--ink);
         font:16px/1.5 system-ui,-apple-system,"Segoe UI",Roboto,sans-serif; }
  a { color:var(--accent-d); text-decoration:none; } a:hover { text-decoration:underline; }
  header { background:var(--card); border-bottom:1px solid var(--line); position:sticky; top:0; z-index:5; }
  .bar { max-width:980px; margin:0 auto; padding:.6rem 1rem; display:flex; gap:1rem;
         align-items:center; flex-wrap:wrap; }
  .brand { font-weight:800; font-size:1.3rem; color:var(--ink); letter-spacing:-.02em; }
  .brand span { color:var(--accent); }
  nav { display:flex; gap:1rem; flex:1; }
  .who { display:flex; gap:.4rem; align-items:center; font-size:.9rem; }
  select, input[type=text], textarea { font:inherit; padding:.45rem .6rem; border:1px solid var(--line);
         border-radius:8px; background:#fff; color:var(--ink); }
  textarea { width:100%; resize:vertical; }
  button { font:inherit; cursor:pointer; border:1px solid var(--line); background:#fff; color:var(--ink);
           padding:.35rem .8rem; border-radius:8px; }
  button:hover { border-color:var(--accent); }
  button.primary { background:var(--accent); border-color:var(--accent); color:#fff; font-weight:600; }
  button.primary:hover { background:var(--accent-d); }
  button.danger { color:var(--danger); border-color:#f0c4c0; }
  button.link { border:0; background:none; padding:0; color:var(--muted); }
  button.link:hover { color:var(--accent-d); text-decoration:underline; }
  main { max-width:980px; margin:1.2rem auto; padding:0 1rem; display:grid;
         grid-template-columns:minmax(0,1fr) 240px; gap:1.2rem; }
  @media (max-width:760px) { main { grid-template-columns:1fr; } }
  .card { background:var(--card); border:1px solid var(--line); border-radius:12px; padding:1rem; margin-bottom:.9rem; }
  .side h3 { margin:.1rem 0 .5rem; font-size:.8rem; text-transform:uppercase; letter-spacing:.06em; color:var(--muted); }
  .side ul { list-style:none; margin:0; padding:0; }
  .side li { display:flex; justify-content:space-between; padding:.15rem 0; }
  .muted { color:var(--muted); font-size:.88rem; }
  .meta { display:flex; gap:.5rem; align-items:baseline; flex-wrap:wrap; }
  .meta strong a { color:var(--ink); }
  .badge { font-size:.7rem; padding:.05rem .45rem; border-radius:99px; border:1px solid var(--line); color:var(--muted); }
  .badge.mod { color:#7c3aed; border-color:#d8c8f8; } .badge.admin { color:var(--danger); border-color:#f0c4c0; }
  .content { margin:.45rem 0; white-space:pre-wrap; overflow-wrap:anywhere; }
  .tag { font-weight:500; }
  .actions { display:flex; gap:1rem; align-items:center; flex-wrap:wrap; font-size:.9rem; }
  .actions form { margin:0; display:inline; }
  .liked { color:var(--accent-d); font-weight:600; }
  .flash { padding:.55rem .9rem; border-radius:8px; margin-bottom:.8rem; font-size:.92rem; }
  .flash.ok { background:#e6f4ea; color:var(--ok); } .flash.error { background:#fdeceb; color:var(--danger); }
  .tabs { display:flex; gap:.4rem; margin-bottom:.9rem; }
  .tabs a { padding:.3rem .9rem; border-radius:99px; border:1px solid var(--line); background:#fff; color:var(--ink); }
  .tabs a.on { background:var(--accent); border-color:var(--accent); color:#fff; }
  .row { display:flex; gap:.5rem; align-items:center; justify-content:space-between; margin-top:.4rem; flex-wrap:wrap; }
  details summary { cursor:pointer; color:var(--muted); list-style:none; } details summary::-webkit-details-marker { display:none; }
  details form { display:flex; gap:.4rem; margin-top:.4rem; }
  details input[type=text] { flex:1; }
  .stats { display:flex; gap:1.4rem; margin:.5rem 0; } .stats b { display:block; font-size:1.2rem; }
  table { width:100%; border-collapse:collapse; font-size:.9rem; } th,td { text-align:left; padding:.4rem .5rem; border-bottom:1px solid var(--line); }
  h1,h2 { margin:.1rem 0 .7rem; } h2 { font-size:1.15rem; }
  .comment { padding:.55rem 0; border-top:1px solid var(--line); } .comment:first-of-type { border-top:0; }
</style>
</head>
<body>
<header><div class="bar">
  <a class="brand" href="{{ url_for('index') }}">Y<span>,</span> Y not</a>
  <nav>
    <a href="{{ url_for('index') }}">Home</a>
    {% if me %}<a href="{{ url_for('profile', username=me.Username) }}">My profile</a>{% endif %}
    {% if staff %}<a href="{{ url_for('moderation') }}">Moderation{% if open_reports %} ({{ open_reports }}){% endif %}</a>{% endif %}
  </nav>
  <form class="who" method="post" action="{{ url_for('login') }}">
    <label for="uid" class="muted">Viewing as</label>
    <select name="uid" id="uid" onchange="this.form.submit()">
      <option value="">Guest</option>
      {% for u in all_users %}
        <option value="{{ u.UserID }}" {{ 'selected' if me and me.UserID == u.UserID }}>
          {{ u.Username }}{% if u.Role != 'user' %} ({{ u.Role }}){% endif %}</option>
      {% endfor %}
    </select>
    <noscript><button>Go</button></noscript>
  </form>
</div></header>

<main>
  <section>
    {% for cat, msg in get_flashed_messages(with_categories=true) %}
      <div class="flash {{ cat }}">{{ msg }}</div>
    {% endfor %}
    {% block content %}{% endblock %}
  </section>
  <aside class="side">
    <div class="card">
      <h3>Trending (last 7 days of data)</h3>
      <ul>
        {% for t in trending %}
          <li><a href="{{ url_for('tag_page', tag=t.Tag) }}">#{{ t.Tag }}</a><span class="muted">{{ t.n }}</span></li>
        {% else %}<li class="muted">Nothing yet</li>{% endfor %}
      </ul>
    </div>
  </aside>
</main>
</body></html>
"""

TEMPLATES["_post.html"] = r"""{% macro post_card(p, detail=False) %}
<article class="card">
  <div class="meta">
    <strong><a href="{{ url_for('profile', username=p.Username) }}">{{ p.Username }}</a></strong>
    {% if p.Role != 'user' %}<span class="badge {{ 'mod' if p.Role == 'moderator' else 'admin' }}">{{ p.Role }}</span>{% endif %}
    {% if p.IsPrivate %}<span class="badge">private</span>{% endif %}
    <a class="muted" href="{{ url_for('post_detail', post_id=p.PostID) }}">{{ p.CreatedAt | when }}</a>
  </div>
  <div class="content">{{ p.Content | linkify }}</div>
  <div class="actions">
    <form method="post" action="{{ url_for('toggle_like', post_id=p.PostID) }}">
      <button class="link {{ 'liked' if p.LikedByMe }}">{{ '♥' if p.LikedByMe else '♡' }} {{ p.LikeCount }}</button>
    </form>
    <a href="{{ url_for('post_detail', post_id=p.PostID) }}#comments">💬 {{ p.CommentCount }}</a>
    {% if me and me.UserID != p.UserID %}
    <details>
      <summary>Report</summary>
      <form method="post" action="{{ url_for('report_post', post_id=p.PostID) }}">
        <input type="text" name="reason" placeholder="Why are you reporting this?" maxlength="200" required>
        <button>Send</button>
      </form>
    </details>
    {% endif %}
  </div>
</article>
{% endmacro %}
"""

TEMPLATES["index.html"] = r"""{% extends "base.html" %}
{% from "_post.html" import post_card with context %}
{% block content %}
{% if me %}
<form class="card" method="post" action="{{ url_for('create_post') }}">
  <textarea name="content" rows="3" maxlength="{{ max_post }}" required
            placeholder="What's on your mind, {{ me.Username }}? Use #hashtags to join a topic."></textarea>
  <div class="row"><span class="muted">Up to {{ max_post }} characters</span><button class="primary">Post</button></div>
</form>
{% endif %}
<div class="tabs">
  <a class="{{ 'on' if mode == 'all' }}" href="{{ url_for('index') }}">Everyone</a>
  {% if me %}<a class="{{ 'on' if mode == 'following' }}" href="{{ url_for('index', feed='following') }}">Following</a>{% endif %}
</div>
{% for p in posts %}{{ post_card(p) }}
{% else %}<div class="card muted">No posts to show.{% if mode == 'following' %} Follow some people to fill this feed!{% endif %}</div>{% endfor %}
{% endblock %}
"""

TEMPLATES["post.html"] = r"""{% extends "base.html" %}
{% from "_post.html" import post_card with context %}
{% block title %}Post #{{ post.PostID }} · Y, Y not{% endblock %}
{% block content %}
<p><a href="{{ url_for('index') }}">&larr; Back</a></p>
{{ post_card(post, True) }}
<div class="card" id="comments">
  <h2>Comments ({{ comments|length }})</h2>
  {% for c in comments %}
    <div class="comment">
      <div class="meta"><strong><a href="{{ url_for('profile', username=c.Username) }}">{{ c.Username }}</a></strong>
        <span class="muted">{{ c.CreatedAt | when }}</span></div>
      <div class="content">{{ c.Body }}</div>
    </div>
  {% else %}<p class="muted">No comments yet.</p>{% endfor %}
  {% if me %}
  <form method="post" action="{{ url_for('add_comment', post_id=post.PostID) }}" class="row">
    <input type="text" name="body" maxlength="{{ max_comment }}" placeholder="Write a comment…" style="flex:1" required>
    <button class="primary">Comment</button>
  </form>
  {% else %}<p class="muted">Pick a user in the top bar to comment.</p>{% endif %}
</div>
{% endblock %}
"""

TEMPLATES["tag.html"] = r"""{% extends "base.html" %}
{% from "_post.html" import post_card with context %}
{% block title %}#{{ tag }} · Y, Y not{% endblock %}
{% block content %}
<h1>#{{ tag }}</h1>
{% for p in posts %}{{ post_card(p) }}
{% else %}<div class="card muted">No visible posts use this hashtag.</div>{% endfor %}
{% endblock %}
"""

TEMPLATES["profile.html"] = r"""{% extends "base.html" %}
{% from "_post.html" import post_card with context %}
{% block title %}{{ user.Username }} · Y, Y not{% endblock %}
{% block content %}
<div class="card">
  <div class="row" style="margin-top:0">
    <div>
      <h1 style="margin:0">{{ user.Username }}
        {% if user.Role != 'user' %}<span class="badge {{ 'mod' if user.Role == 'moderator' else 'admin' }}">{{ user.Role }}</span>{% endif %}
        {% if user.IsPrivate %}<span class="badge">private</span>{% endif %}</h1>
      <div class="muted">Joined {{ user.CreatedAt | when }}</div>
    </div>
    {% if me and me.UserID != user.UserID %}
    <form method="post" action="{{ url_for('toggle_follow', user_id=user.UserID) }}">
      {% if not follow %}<button class="primary">Follow</button>
      {% elif follow.Status == 'pending' %}<button>Requested · cancel</button>
      {% else %}<button>Following ✓ · unfollow</button>{% endif %}
    </form>
    {% endif %}
  </div>
  <div class="stats">
    <div><b>{{ stats.PostCount }}</b><span class="muted">posts</span></div>
    <div><b>{{ stats.FollowerCount }}</b><span class="muted">followers</span></div>
    <div><b>{{ stats.FollowingCount }}</b><span class="muted">following</span></div>
  </div>
</div>

{% if requests_in %}
<div class="card">
  <h2>Follow requests</h2>
  {% for r in requests_in %}
  <div class="row">
    <span><a href="{{ url_for('profile', username=r.RequesterUsername) }}">{{ r.RequesterUsername }}</a>
      <span class="muted">· {{ r.CreatedAt | when }}</span></span>
    <form method="post" action="{{ url_for('respond_follow_request', follower_id=r.FollowerID) }}" style="display:flex;gap:.4rem">
      <button class="primary" name="action" value="accept">Accept</button>
      <button name="action" value="decline">Decline</button>
    </form>
  </div>
  {% endfor %}
</div>
{% endif %}

{% if visible %}
  {% for p in posts %}{{ post_card(p) }}
  {% else %}<div class="card muted">No posts yet.</div>{% endfor %}
{% else %}
  <div class="card muted">🔒 This account is private. Follow {{ user.Username }} and wait for approval to see their posts.</div>
{% endif %}
{% endblock %}
"""

TEMPLATES["mod.html"] = r"""{% extends "base.html" %}
{% block title %}Moderation · Y, Y not{% endblock %}
{% block content %}
<h1>Moderation queue</h1>
{% for item in queue %}
<div class="card">
  <div class="meta"><strong>Post #{{ item.PostID }}</strong> by
    <a href="{{ url_for('profile', username=item.AuthorUsername) }}">{{ item.AuthorUsername }}</a>
    <span class="badge admin">{{ item.ReportCount }} open report{{ 's' if item.ReportCount != 1 }}</span></div>
  <div class="content">{{ item.Content }}</div>
  <table>
    <tr><th>Reporter</th><th>Reason</th><th>When</th></tr>
    {% for r in item.Reports %}<tr><td>{{ r.Reporter }}</td><td>{{ r.Reason }}</td><td>{{ r.CreatedAt | when }}</td></tr>{% endfor %}
  </table>
  <div class="row">
    <a href="{{ url_for('post_detail', post_id=item.PostID) }}">View post</a>
    <span style="display:flex;gap:.4rem">
      <form method="post" action="{{ url_for('mod_dismiss', post_id=item.PostID) }}"><button>Dismiss reports</button></form>
      <form method="post" action="{{ url_for('mod_remove', post_id=item.PostID) }}"
            onsubmit="return confirm('Remove this post? Its content is replaced and hashtags detached.')">
        <button class="danger">Remove post</button></form>
    </span>
  </div>
</div>
{% else %}<div class="card muted">Queue is empty. 🎉</div>{% endfor %}

<h2>Review history</h2>
<div class="card">
<table>
  <tr><th>#</th><th>Post</th><th>Reporter</th><th>Reason</th><th>Outcome</th><th>By</th></tr>
  {% for r in history %}
  <tr><td>{{ r.ReportID }}</td><td><a href="{{ url_for('post_detail', post_id=r.PostID) }}">#{{ r.PostID }}</a></td>
      <td>{{ r.Reporter }}</td><td>{{ r.Reason }}</td><td>{{ r.Status }}</td><td>{{ r.Reviewer }}</td></tr>
  {% else %}<tr><td colspan="6" class="muted">Nothing reviewed yet.</td></tr>{% endfor %}
</table></div>
{% endblock %}
"""

TEMPLATES["error.html"] = r"""{% extends "base.html" %}
{% block content %}<div class="card"><h1>{{ code }}</h1><p>{{ msg }}</p><a href="{{ url_for('index') }}">Back home</a></div>{% endblock %}
"""

app.jinja_loader = DictLoader(TEMPLATES)


if __name__ == "__main__":
    init_db_if_missing()
    app.run(debug=True)
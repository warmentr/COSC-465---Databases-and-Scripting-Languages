# Y, Y not

A small text-based social media database project with a Flask web frontend.
DBMS: SQLite 3.

## Files

| File | Purpose |
|------|---------|
| `schema.sql` | Creates the tables, indexes, and views |
| `insert_data.sql` | Fills the database with sample data (movie fan pages, plus one moderator and one admin) |
| `queries.sql` | The Deliverable 4 queries |
| `transaction.sql` | Moderation transaction demo (ends in `ROLLBACK`) |
| `run_queries.sh` | Rebuilds the database and runs the queries and transaction |
| `app.py` | Single-file Flask web frontend |

## Requirements

- Python 3.8+
- Flask: `pip install flask`
- SQLite 3 command-line tool (only needed for the SQL scripts, not for the web app)

## Set up the database

```bash
sqlite3 yynot.db
> .read schema.sql
> .read insert_data.sql
> .quit
```

(If you skip this step, `app.py` builds `yynot.db` automatically from `schema.sql` and `insert_data.sql` when it first runs.)

## Run the web app

Make sure `app.py` is in the same folder as `yynot.db`, then:

```bash
pip install flask
python app.py
```

Open http://127.0.0.1:5000 in a browser.

There are no passwords, so use the **Viewing as** dropdown in the top bar to switch users:

- `honey_hive_hq`, `truffula_trees_4ever`, `rebel_alliance_rae`, `one_ring_ron`: regular users
- `spice_must_flow`: private account (posts are only visible to accepted followers)
- `mod_mira`: moderator (can open the **Moderation** page)
- `admin_alex`: admin (same moderation access)

## Run the SQL queries and transaction demo

```bash
bash run_queries.sh
```

This deletes and recreates `yynot.db`, runs `queries.sql`, then runs `transaction.sql`.

## Reset the data

Using the web app changes `yynot.db`. To go back to the original sample data:

```bash
bash run_queries.sh
```

or delete `yynot.db` and rerun the "Set up the database" steps.
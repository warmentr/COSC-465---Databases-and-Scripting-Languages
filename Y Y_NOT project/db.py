# Database connection helper for the Y, Y not application.
import os
import sqlite3

# Default: yynot.db next to this file. Override with the YYNOT_DB environment
# variable or by passing a path as the first command-line argument.
DEFAULT_DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "yynot.db")


class DatabaseNotFound(Exception):
    """Raised when the SQLite file does not exist."""


def get_connection(path=None):
    path = path or os.environ.get("YYNOT_DB") or DEFAULT_DB_PATH
    if not os.path.isfile(path):
        raise DatabaseNotFound(
            f"Database file not found: {path}\n"
            "Create it first with:  sqlite3 yynot.db < schema.sql  and  "
            "sqlite3 yynot.db < insert_data.sql"
        )
    conn = sqlite3.connect(path)
    conn.row_factory = sqlite3.Row          # access columns by name
    conn.execute("PRAGMA foreign_keys = ON")  # SQLite leaves this off by default
    return conn
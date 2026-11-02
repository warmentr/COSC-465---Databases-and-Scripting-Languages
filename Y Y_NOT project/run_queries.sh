#!/bin/bash
# Recreates the Y, Y not database and runs all Deliverable 4 files.
# DBMS: SQLite 3. Run with: bash run_queries.sh

cd "$(dirname "$0")" || exit 1   # so it works from any directory

DB="yynot.db"

if ! command -v sqlite3 >/dev/null 2>&1; then
    echo "sqlite3 is not installed or not on PATH."
    exit 1
fi

echo "Recreating database with schema.sql and insert_data.sql"
rm -f "$DB"
sqlite3 -bail "$DB" < schema.sql      || { echo "schema.sql failed.";      exit 1; }
sqlite3 -bail "$DB" < insert_data.sql || { echo "insert_data.sql failed."; exit 1; }

echo
echo "Running queries with queries.sql"
sqlite3 -header -column "$DB" < queries.sql

echo
echo "Running transaction with transaction.sql"
sqlite3 -bail "$DB" < transaction.sql
status=$?

if [ "$status" -eq 0 ]; then
    echo
    echo "Transaction demo finished with no errors (it ends in ROLLBACK, so the database is unchanged)."
else
    echo
    echo "Transaction failed. Uncommitted changes were rolled back."
fi

echo
echo "Done."
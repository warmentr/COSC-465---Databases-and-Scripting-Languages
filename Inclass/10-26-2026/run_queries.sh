#!/bin/bash

DB="demo3c.db"
# DB="$1"

echo "Recreating database..."

# TODO: Remove the old database
rm -f "$DB"

# TODO: Run schema.sql
sqlite3 "$DB" < schema.sql

# TODO: Run insert_data.sql
sqlite3 "$DB" < insert_data.sql

echo
echo "Running queries..."

# TODO: Run queries.sql
# Display column headings and format the output as columns.
sqlite3 -header -column "$DB" < queries.sql

echo
echo "Running transaction..."

# TODO: Run transaction.sql
sqlite3 -bail "$DB" < transaction.sql
status=$?

if [ "$status" -eq 0 ]; then
    echo "Transaction completed successfully."
else
    echo "Transaction failed."
    echo "Uncommitted changes were rolled back."
fi 

echo
echo "Done."
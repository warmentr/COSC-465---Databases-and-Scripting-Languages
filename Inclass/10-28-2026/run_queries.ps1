$DB = "demo3c.db"
# DB = $args[0]

Write-Output "Recreating database..."

Remove-Item -Path $DB -Force -ErrorAction SilentlyContinue

sqlite3 $DB ".read schema.sql"
sqlite3 $DB ".read insert_data.sql"

Write-Output ""
Write-Output "Running queries..."

# Display column headings and format the output as columns.
sqlite3 -header -column $DB ".read queries.sql"

Write-Output ""
Write-Output "Running transaction..."

sqlite3 -bail $DB ".read transaction.sql"
$status = $LASTEXITCODE

if ( $status -eq 0 ) {
    Write-Output "Transaction completed successfully."
} else {
    Write-Output "Transaction failed."
    Write-Output "Uncommitted changes were rolled back."
}

Write-Output ""
Write-Output "Done."
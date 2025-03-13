#!/bin/bash

# Ensure a title argument is provided
if [ -z "$1" ]; then
    echo "Usage: $0 <migration_title>"
    exit 1
fi

# Get the current Unix timestamp
TIMESTAMP=$(date +%s)

# Convert title to lowercase, replace spaces with underscores, and remove special characters
TITLE=$(echo "$1" | tr '[:upper:]' '[:lower:]' | tr ' ' '_' | sed 's/[^a-z0-9_]//g')

# Define migration file path
MIGRATION_DIR="migrations/sqlite"
MIGRATION_FILE="${MIGRATION_DIR}/${TIMESTAMP}_${TITLE}.sql"

# Ensure migration directory exists
mkdir -p "$MIGRATION_DIR"

# Create the migration file
touch "$MIGRATION_FILE"

# Print confirmation message
echo "✅ Migration file created: $MIGRATION_FILE"

# Open file in nano (optional, remove if not needed)
nano "$MIGRATION_FILE"

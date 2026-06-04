#!/usr/bin/env bash
set -euo pipefail

BACKUP_DIR="backups"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
DB_FILE="db.sqlite3"
OUT="$BACKUP_DIR/db_$TIMESTAMP.sqlite3"

mkdir -p "$BACKUP_DIR"

if [ ! -f "$DB_FILE" ]; then
    echo "db.sqlite3 not found" >&2
    exit 1
fi

cp "$DB_FILE" "$OUT"
echo "backup saved: $OUT"

find "$BACKUP_DIR" -name "db_*.sqlite3" -mtime +7 -delete

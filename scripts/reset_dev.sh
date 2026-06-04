#!/usr/bin/env bash
set -euo pipefail

PY="myworld/bin/python"

read -rp "Reset database and media? All data will be lost. [y/N] " confirm
[ "$confirm" = "y" ] || exit 0

rm -f db.sqlite3
find . -path "*/migrations/0*.py" ! -path "./myworld/*" -delete

$PY manage.py makemigrations
$PY manage.py migrate
$PY manage.py createsuperuser

echo "dev environment reset"

#!/usr/bin/env bash
# Exit on error
set -o errexit

# Install dependencies
pip install -r requirements.txt

echo "💣 Wiping Database..."
python manage.py shell -c "from django.db import connection; cursor = connection.cursor(); cursor.execute('DROP SCHEMA public CASCADE; CREATE SCHEMA public;');"
echo "💣 Database wiped."

# --- OPTIONAL: Force remove pycache ---
find . -type d -name "__pycache__" -exec rm -r {} +

# Convert static asset files
python manage.py collectstatic --no-input

# Apply any outstanding database migrations
python manage.py migrate

python manage.py createsuperuser --no-input || true
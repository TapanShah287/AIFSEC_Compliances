#!/usr/bin/env bash
# Exit on error
set -o errexit

# Install dependencies
pip install -r requirements.txt

# --- OPTIONAL: Force remove pycache ---
find . -type d -name "__pycache__" -exec rm -r {} +

# Convert static asset files
python manage.py collectstatic --no-input

# Apply any outstanding database migrations
python manage.py migrate

python manage.py createsuperuser --no-input || true
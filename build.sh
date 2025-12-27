#!/usr/bin/env bash
# Exit on error
set -o errexit

# Install dependencies
pip install -r requirements.txt

# Convert static asset files
python manage.py collectstatic --no-input

# Apply any outstanding database migrations
python manage.py migrate

# OPTIONAL: Create superuser automatically (as discussed earlier)
#python manage.py createsuperuser --no-input || true
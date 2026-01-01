#!/bin/bash
set -e

echo "Running migrations..."
python manage.py migrate --noinput

echo "Setting up admin user..."
python manage.py setup_admin

exec "$@"

#!/bin/bash
set -e

echo "Waiting for database to be ready..."
while ! python -c "import pymysql; pymysql.connect(host='${DB_HOST:-db}', user='${DB_USER:-root}', password='${DB_PASSWORD:-rootpassword}', database='${DB_NAME:-license_server}')" 2>/dev/null; do
    echo "Database not ready, waiting..."
    sleep 2
done
echo "Database is ready!"

echo "Running migrations..."
python manage.py migrate --noinput

echo "Collecting static files..."
python manage.py collectstatic --noinput

echo "Setting up admin user..."
python manage.py setup_admin || true

echo "Starting application..."
exec "$@"

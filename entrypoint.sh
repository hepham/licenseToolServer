#!/bin/bash
set -e

# Fix permissions on mounted volumes (runs as root initially)
echo "Fixing volume permissions..."
mkdir -p /app/keys
chown -R appuser:appuser /app/staticfiles /app/keys 2>/dev/null || true

# Switch to appuser for the rest of the script
exec gosu appuser bash -c '
set -e

echo "Waiting for database to be ready..."
while ! python -c "import pymysql; pymysql.connect(host=\"${DB_HOST:-db}\", user=\"${DB_USER:-root}\", password=\"${DB_PASSWORD:-rootpassword}\", database=\"${DB_NAME:-license_server}\")" 2>/dev/null; do
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

echo "Generating signing keys if not exist..."
python manage.py generate_signing_keys || true

echo "Starting application..."
exec "$@"
' -- "$@"

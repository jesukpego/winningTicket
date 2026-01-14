#!/bin/bash
set -e

PORT=${PORT:-8000}

echo "=== Starting Winning Ticket Django App ==="
echo "Port: $PORT"

# Apply database migrations
echo "Applying migrations..."
python manage.py migrate --noinput

# Collect static files
echo "Collecting static files..."
python manage.py collectstatic --noinput

# Start Gunicorn
echo "Starting Gunicorn..."
exec gunicorn config.wsgi:application \
    --bind 0.0.0.0:$PORT \
    --workers 2 \
    --timeout 180 \
    --log-level info \
    --access-logfile - \
    --error-logfile -

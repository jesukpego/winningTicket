#!/bin/sh
set -e

# Railway fournit le PORT automatiquement
PORT=${PORT:-8000}

echo "=== Starting Winning Ticket Django App ==="
echo "Port: $PORT"

# Appliquer les migrations
echo "Applying migrations..."
python manage.py migrate --noinput

# Collecter les fichiers statiques
echo "Collecting static files..."
python manage.py collectstatic --noinput

# Lancer Gunicorn
echo "Starting Gunicorn..."
exec gunicorn config.wsgi:application \
    --bind 0.0.0.0:$PORT \
    --workers 2 \
    --timeout 180 \
    --log-level info \
    --access-logfile - \
    --error-logfile -

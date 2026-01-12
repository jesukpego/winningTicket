#!/bin/bash
set -e

PORT=${PORT:-8000}

echo "=== Starting Winning Ticket Django App ==="
echo "Port: $PORT"
echo "Debug: $DEBUG"

# Wait for database (if using PostgreSQL)
if [ ! -z "$DATABASE_URL" ]; then
    echo "Waiting for database..."
    sleep 2
fi

# Apply database migrations
echo "Applying migrations..."
python manage.py migrate --noinput

# Collect static files
echo "Collecting static files..."
python manage.py collectstatic --noinput

# Create superuser if not exists (optional)
echo "from django.contrib.auth import get_user_model; User = get_user_model(); User.objects.filter(username='admin').exists() or User.objects.create_superuser('admin', 'admin@example.com', 'admin')" | python manage.py shell || true

# Start Gunicorn with proper settings for Railway
echo "Starting Gunicorn..."
exec gunicorn config.wsgi:application \
    --bind 0.0.0.0:$PORT \
    --workers 2 \
    --timeout 120 \
    --keepalive 5 \
    --max-requests 1000 \
    --max-requests-jitter 50 \
    --log-level info \
    --access-logfile - \
    --error-logfile -
    
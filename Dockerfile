# Base image
FROM python:3.11-slim

# Set workdir
WORKDIR /app

# Copy files
COPY requirements.txt .

# Upgrade pip et installer les packages
RUN python -m pip install --upgrade pip
RUN pip install -r requirements.txt

# Copy project
COPY . .

# Gunicorn command
CMD ["gunicorn", "config.wsgi:application", "--bind", "0.0.0.0:8000", "--workers", "3"]

FROM python:3.11-slim

# Set work directory
WORKDIR /app

# Copy requirements
COPY requirements.txt .

# Upgrade pip
RUN python -m pip install --upgrade pip

# Install dependencies
RUN pip install -r requirements.txt

# Copy project files
COPY . .

# Make start.sh executable
RUN chmod +x start.sh

# Set environment variable for Django
ENV PYTHONUNBUFFERED=1

# Start the app
CMD ["./start.sh"]

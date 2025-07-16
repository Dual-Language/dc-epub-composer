FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create storage directory
RUN mkdir -p /app/storage

# Set environment variables
ENV STORAGE_ROOT=/app/storage
ENV SLEEP_INTERVAL=10
ENV DEFAULT_COMPOSER=simple_markdown

# Run the service
CMD ["python", "main.py"] 
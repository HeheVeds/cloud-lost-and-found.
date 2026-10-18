# ==============================================================================
# Dockerfile for Cloud-Based Lost and Found Management System
# Demonstrates: Containerization & Cloud Deployment on AWS EC2
# ==============================================================================

# Use official lightweight Python runtime
FROM python:3.11-slim

# Set environment flags
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    RUNNING_IN_DOCKER=true \
    PORT=5000

# Set container working directory
WORKDIR /app

# Install system dependencies (build-essential, curl for healthchecks)
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy dependency definition first to leverage Docker layer caching
COPY requirements.txt .

# Install Python packages
RUN pip install --no-cache-dir -r requirements.txt

# Copy application source code
COPY . .

# Ensure upload directory exists inside container
RUN mkdir -p /app/app/static/uploads

# Expose network port to the Docker host
EXPOSE 5000

# Run production WSGI server (Gunicorn) with 2 workers
CMD ["gunicorn", "--bind", "0.0.0.0:5000", "--workers", "2", "--timeout", "120", "run:app"]

FROM python:3.9-slim as base

# Set working directory
WORKDIR /app

# Copy requirements files
COPY requirements.txt backend-requirements.txt

# Install dependencies
RUN pip install --no-cache-dir -r backend-requirements.txt -r frontend-requirements.txt

# Install supervisor
RUN apt-get update && apt-get install -y supervisor && rm -rf /var/lib/apt/lists/*

# Copy application code
COPY backend/ backend/
COPY frontend/ frontend/

# Create supervisor configuration
RUN mkdir -p /var/log/supervisor
COPY supervisord.conf /etc/supervisor/conf.d/supervisord.conf

# Expose ports
EXPOSE 8000 8501

# Start supervisor
CMD ["/usr/bin/supervisord", "-c", "/etc/supervisor/conf.d/supervisord.conf"]
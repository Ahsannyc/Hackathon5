# CloudFlow Production Docker Image
# Build: docker build -t cloudflow:latest .
# Run: docker run -p 5000:5000 cloudflow:latest

FROM python:3.11-slim

LABEL maintainer="CloudFlow Team <support@cloudflow.io>"
LABEL version="1.0.0"
LABEL description="CloudFlow Customer Success AI Employee - Production"

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create non-root user for security
RUN useradd -m -u 1000 cloudflow
USER cloudflow

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import requests; requests.get('http://localhost:5000/health')" || exit 1

# Expose port
EXPOSE 5000

# Run application
CMD ["python", "-m", "production.api.mcp_tools"]

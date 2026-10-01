# GRC_Claw Dockerfile
FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    libpq-dev \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY src/grcclaw/ ./grcclaw/
COPY config/ ./config/

# Create non-root user
RUN useradd -m -r grcclaw && chown -R grcclaw:grcclaw /app
USER grcclaw

# Expose port
EXPOSE 8080

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8080/health || exit 1

# Run the API server
CMD ["uvicorn", "grcclaw.api:app", "--host", "0.0.0.0", "--port", "8080", "--workers", "4"]

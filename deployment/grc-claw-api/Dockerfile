FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    libpq-dev \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY pyproject.toml requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Generate gRPC code (if proto files exist)
RUN if [ -f proto/grc_claw.proto ]; then \
    python -m grpc_tools.protoc -I./proto --python_out=. --grpc_python_out=. proto/grc_claw.proto || true; \
    fi

EXPOSE 8080 50051

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8080", "--workers", "4"]

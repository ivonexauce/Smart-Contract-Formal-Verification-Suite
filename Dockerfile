FROM python:3.11-slim

LABEL maintainer="UMBA Consulting Engineers"
LABEL description="Smart Contract Formal Verification Suite"

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    curl \
    git \
    && rm -rf /var/lib/apt/lists/*

# Create app directory
WORKDIR /app

# Copy dependencies first for layer caching
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create reports directory
RUN mkdir -p reports

# Default command
CMD ["python", "scripts/run_full_audit.py", "--help"]

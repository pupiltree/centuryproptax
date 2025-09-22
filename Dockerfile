# Production Dockerfile for Century Property Tax Documentation Portal
# Optimized for security, performance, and reliability

FROM python:3.11-slim as base

# Security: Create non-root user
RUN groupadd -r appuser && useradd -r -g appuser appuser

# Install system dependencies with security updates
RUN apt-get update && apt-get install -y \
    --no-install-recommends \
    curl \
    build-essential \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy requirements first for better caching
COPY requirements.txt .

# Install Python dependencies with security optimizations
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create necessary directories with proper permissions
RUN mkdir -p logs && \
    mkdir -p docs/static && \
    chown -R appuser:appuser /app

# Production stage
FROM base as production

# Security: Switch to non-root user
USER appuser

# Environment variables for production
ENV PYTHONPATH=/app
ENV PYTHONUNBUFFERED=1
ENV ENVIRONMENT=production
ENV PORT=8000

# Health check
HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:${PORT}/health || exit 1

# Expose port
EXPOSE ${PORT}

# Production command with optimizations
CMD ["gunicorn", "--worker-class", "uvicorn.workers.UvicornWorker", \
     "--workers", "4", "--worker-connections", "1000", \
     "--max-requests", "10000", "--max-requests-jitter", "1000", \
     "--preload", "--bind", "0.0.0.0:8000", \
     "--access-logfile", "-", "--error-logfile", "-", \
     "--log-level", "info", "src.main:app"]
# Multi-stage Dockerfile for Banking Client
# Optimized for production use with minimal image size

# Build stage
FROM python:3.12-slim AS builder

WORKDIR /build

# Copy requirements and install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir --prefix=/install -r requirements.txt

# Runtime stage
FROM python:3.12-slim

WORKDIR /app

# Copy installed packages from builder
COPY --from=builder /install /usr/local

# Copy application code
COPY banking_client/ ./banking_client/
COPY main.py .
COPY example_usage.py .
COPY check_server.py .

# Set Python to run in unbuffered mode
ENV PYTHONUNBUFFERED=1

# Default environment variables (can be overridden)
ENV API_BASE_URL=http://localhost:8123
ENV ENABLE_AUTHENTICATION=false
ENV LOG_LEVEL=INFO

# Create non-root user for security
RUN useradd -m -u 1000 bankinguser && \
    chown -R bankinguser:bankinguser /app

USER bankinguser

# Health check
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
    CMD python check_server.py || exit 1

# Default command - run CLI help
ENTRYPOINT ["python", "main.py"]
CMD ["--help"]

# Example usage:
# docker build -t banking-client .
# docker run banking-client transfer --from ACC1000 --to ACC1001 --amount 100
# docker run -e ENABLE_AUTHENTICATION=true banking-client list


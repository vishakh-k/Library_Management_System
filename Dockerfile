# ==============================================================================
# Dockerfile – Library Management System
# Multi-stage build for a production-ready Flask application
# ==============================================================================

# --------------- Stage 1: Builder ---------------
FROM python:3.11-slim AS builder

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app

# Install system dependencies required to compile mysqlclient and other C
# extensions. Kept in a separate stage so the final image stays small.
RUN apt-get update && apt-get install -y --no-install-recommends \
    default-libmysqlclient-dev \
    build-essential \
    pkg-config \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir --prefix=/install -r requirements.txt

# --------------- Stage 2: Runtime ---------------
FROM python:3.11-slim

LABEL maintainer="Library Management System Team"
LABEL description="Production image for Library Management System"

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV FLASK_ENV=production

WORKDIR /app

# Install only the runtime library for MySQL (no compiler toolchain)
RUN apt-get update && apt-get install -y --no-install-recommends \
    default-libmysqlclient-dev \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Create a non-root user for running the application
RUN groupadd -r appuser && useradd -r -g appuser -d /app -s /sbin/nologin appuser

# Copy pre-built Python packages from the builder stage
COPY --from=builder /install /usr/local

# Copy application source code
COPY . .

# Ensure the static and logs directories exist and are owned by appuser
RUN mkdir -p /app/static /app/logs \
    && chmod +x deployment/entrypoint.sh \
    && chown -R appuser:appuser /app

USER appuser

EXPOSE 5000

# Health-check: verify the app responds on /
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD curl -f http://localhost:5000/ || exit 1

ENTRYPOINT ["/app/deployment/entrypoint.sh"]
CMD ["gunicorn", "--config", "deployment/gunicorn.conf.py", "app:create_app()"]

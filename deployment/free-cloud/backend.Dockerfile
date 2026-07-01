# Stage 1: Build dependencies
FROM python:3.13-slim as builder

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

COPY backend/requirements.txt .
RUN pip wheel --no-cache-dir --no-deps --wheel-dir /app/wheels -r requirements.txt

# Stage 2: Final runtime image
FROM python:3.13-slim

WORKDIR /app

# Install libpq5 for PostgreSQL and supervisor to run multiple processes
RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq5 \
    supervisor \
    && rm -rf /var/lib/apt/lists/*

COPY --from=builder /app/wheels /wheels
COPY --from=builder /app/requirements.txt .
RUN pip install --no-cache /wheels/*

# Copy backend code
COPY backend ./backend

# Copy supervisor config
COPY deployment/free-cloud/supervisord.conf /etc/supervisor/conf.d/supervisord.conf

ENV PYTHONPATH=/app

# Expose port
EXPOSE 8000

# Run Alembic migrations then start supervisord to manage FastAPI and Celery
CMD ["bash", "-c", "alembic -c backend/alembic.ini upgrade head && /usr/bin/supervisord -c /etc/supervisor/conf.d/supervisord.conf"]

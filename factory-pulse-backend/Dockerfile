# factory-pulse-backend/Dockerfile
FROM python:3.12-slim

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# System deps (PostgreSQL client libs, build tools)
RUN apt-get update && apt-get install -y \
    gcc \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Python dependencies (keep this separate to leverage Docker cache)
COPY requirements .
RUN pip install --no-cache-dir -r requirements

# Application source
COPY . .

# Django default port
EXPOSE 8000

# Bind to 0.0.0.0 so it's reachable outside the container
CMD ["python", "manage.py", "runserver", "0.0.0.0:8000"]

FROM python:3.12-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    libjpeg-dev \
    zlib1g-dev \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install Python requirements
COPY backend/requirements.txt /app/backend/requirements.txt
RUN pip install --no-cache-dir -r /app/backend/requirements.txt

# Copy backend code, data files, and seed assets
COPY backend/ /app/backend/
COPY data/ /app/data/
COPY assets/ /app/assets/
COPY seed_shows.json /app/seed_shows.json
COPY reference.json /app/reference.json

# Copy and setup entrypoint script
COPY backend/entrypoint.sh /app/entrypoint.sh
RUN chmod +x /app/entrypoint.sh

ENV PYTHONPATH=/app
ENV STORAGE_TYPE=local
ENV LOCAL_STORAGE_DIR=/app/storage

# Create storage directory for artwork and live catalogue.json
RUN mkdir -p /app/storage

EXPOSE 8000

ENTRYPOINT ["/app/entrypoint.sh"]

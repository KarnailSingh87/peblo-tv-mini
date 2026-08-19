#!/bin/bash
set -e

echo "=== Starting Peblo TV Backend Service ==="

# Wait for PostgreSQL to become available
echo "Waiting for PostgreSQL database..."
python -c "
import sys, time, os
from sqlalchemy import create_engine

db_url = os.environ.get('DATABASE_URL')
if not db_url:
    print('No DATABASE_URL set, skipping db wait')
    sys.exit(0)

engine = create_engine(db_url)
retries = 30
while retries > 0:
    try:
        with engine.connect() as conn:
            print('Successfully connected to PostgreSQL!')
            sys.exit(0)
    except Exception as e:
        print(f'Waiting for db ({retries} remaining)... {e}')
        time.sleep(1)
        retries -= 1

print('Failed to connect to database in time!')
sys.exit(1)
"

# Run database migrations
echo "Running Alembic database migrations..."
alembic upgrade head

# Seed development users & catalog data
echo "Checking and seeding initial development data..."
python -m backend.app.db.seed || echo "Seed execution completed."

echo "Starting Uvicorn web server on port 8000..."
exec uvicorn backend.app.main:app --host 0.0.0.0 --port 8000

#!/bin/bash
set -euo pipefail

cd /app

echo "Waiting for database to be ready..."
db_ready=0

for i in $(seq 1 30); do
  if python wait_for_db.py >/dev/null 2>&1; then
    echo "Database is ready."
    db_ready=1
    break
  fi
  echo "Database not ready yet, retrying ($i/30)..."
  sleep 2
done

if [ "$db_ready" -ne 1 ]; then
  echo "Database is not ready after 30 attempts. Exiting."
  exit 1
fi

echo "Running database migrations..."
cd /app/bot
alembic upgrade head

echo "Starting Telegram bot..."
exec python bot/main.py
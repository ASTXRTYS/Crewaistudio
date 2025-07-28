#!/bin/bash
# Docker Entrypoint - Runs migrations before starting app
# Created: 2025-01-29

set -e

echo "🚀 Starting AUREN LangGraph Runtime..."

# Wait for PostgreSQL to be ready
echo "⏳ Waiting for PostgreSQL..."
until PGPASSWORD=$DB_PASSWORD psql -h "$DB_HOST" -U "$DB_USER" -d "$DB_NAME" -c '\q' 2>/dev/null; do
  >&2 echo "PostgreSQL is unavailable - sleeping"
  sleep 1
done

echo "✅ PostgreSQL is ready!"

# Run database migrations
echo "🔄 Running database migrations..."
alembic upgrade head

# Run any additional setup scripts
if [ -f "/app/scripts/init_langgraph.py" ]; then
    echo "🔧 Running LangGraph initialization..."
    python /app/scripts/init_langgraph.py
fi

# Start the application
echo "🎯 Starting AUREN application..."
exec "$@" 
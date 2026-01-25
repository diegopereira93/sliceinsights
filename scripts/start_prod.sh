#!/bin/bash
set -e

echo "🚀 Starting Production Boot Sequence..."

# 1. Run migrations
echo "🛠️  Running database migrations..."
alembic upgrade head

# 2. Run seed (if database is empty or force enabled)
# Note: seed_data_hybrid.py handles skipping if SEED_FORCE_CLEAR is not true, 
# but it still adds new data if missing.
echo "🌱 Seeding database..."
python -m app.db.seed_data_hybrid

# 3. Start Application
echo "📡 Starting server..."
exec uvicorn app.main:app --host 0.0.0.0 --port 8000

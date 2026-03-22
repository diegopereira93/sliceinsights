#!/bin/bash
set -e

echo "Waiting for PostgreSQL to be ready..."
until PGPASSWORD=$POSTGRES_PASSWORD psql -h postgres -U $POSTGRES_USER -d $POSTGRES_DB -c '\q' 2>/dev/null; do
    echo "PostgreSQL is unavailable - sleeping"
    sleep 1
done
echo "PostgreSQL is up - continuing"

echo "Running database migrations..."
alembic upgrade head

echo "Seeding stores..."
python scripts/seed_stores.py

echo "Running scrapers..."
for scraper in scripts/scrape_*.py; do
    if [ "$(basename $scraper)" != "scraper_utils.py" ]; then
        echo "Running $(basename $scraper)..."
        python "$scraper" || echo "Warning: $(basename $scraper) failed, continuing..."
    fi
done

echo "Seed complete! Starting application..."
exec "$@"

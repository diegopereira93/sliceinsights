#!/bin/bash
set -e

echo "Waiting for PostgreSQL to be ready..."
until python -c "import psycopg2; psycopg2.connect(host='postgres', user='$POSTGRES_USER', password='$POSTGRES_PASSWORD', dbname='$POSTGRES_DB')" 2>/dev/null; do
    echo "PostgreSQL is unavailable - sleeping"
    sleep 1
done
echo "PostgreSQL is up - continuing"

TABLE_EXISTS=$(python -c "
import psycopg2
conn = psycopg2.connect(host='postgres', user='$POSTGRES_USER', password='$POSTGRES_PASSWORD', dbname='$POSTGRES_DB')
cur = conn.cursor()
cur.execute(\"SELECT COUNT(*) FROM information_schema.tables WHERE table_schema='public' AND table_name='paddle_master'\")
print(cur.fetchone()[0])
cur.close()
conn.close()
")

if [ "$TABLE_EXISTS" = "1" ]; then
    echo "Database already initialized, skipping seed..."
else
    echo "Creating database tables from models..."
    python -c "from app.db.database import init_db_sync; init_db_sync()"

    echo "Running database migrations..."
    alembic upgrade head

    echo "Seeding stores..."
    python scripts/seed_stores.py

    if [ -d "/app/data/db" ] && [ -n "$(ls -A /app/data/db/*.csv 2>/dev/null)" ]; then
        echo "Loading seed data from CSV files..."
        python scripts/seed_from_csv.py
    else
        echo "No CSV seed found, running scrapers (requires network)..."
        for scraper in /app/scripts/scrape_*.py; do
            if [ "$(basename $scraper)" != "scraper_utils.py" ]; then
                echo "Running $(basename $scraper)..."
                python "$scraper" || echo "Warning: $(basename $scraper) failed, continuing..."
            fi
        done
        echo "Exporting DB to CSV for future fast startups..."
        python scripts/export_db_to_csv.py || true
    fi
fi

echo "Seed complete! Starting application..."
exec "$@"

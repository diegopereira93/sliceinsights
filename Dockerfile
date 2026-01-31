FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code and resources
COPY app/ ./app/
COPY data/ ./data/
COPY scripts/ ./scripts/
COPY alembic/ ./alembic/
COPY alembic.ini .

# Make scripts executable
RUN chmod +x scripts/*.sh

# Default port for Railway/Render
ENV PORT=8000
EXPOSE 8000

# Run the application startup script (includes migrations and seeding)
CMD ["./scripts/start_prod.sh"]

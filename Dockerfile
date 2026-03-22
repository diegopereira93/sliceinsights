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

# Make init script executable
RUN chmod +x /app/scripts/init-db.sh

# Default port for Railway/Render
ENV PORT=8000
EXPOSE 8000

# Run the application startup
CMD ["/app/scripts/init-db.sh", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "${PORT}"]

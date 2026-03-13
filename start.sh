#!/bin/bash
set -e

# Auto-ingest if FAISS index doesn't exist
if [ ! -d "/app/data/faiss" ] || [ -z "$(ls -A /app/data/faiss 2>/dev/null)" ]; then
    echo "FAISS index not found, running ingest..."
    python -m app.cli ingest
    echo "Ingest complete."
fi

# Start Telegram bot in background if token is set
if [ -n "$TELEGRAM_BOT_TOKEN" ]; then
    echo "Starting Telegram bot..."
    python -m app.cli telegram-bot &
fi

exec uvicorn app.api.main:app --host 0.0.0.0 --port ${PORT:-8000}

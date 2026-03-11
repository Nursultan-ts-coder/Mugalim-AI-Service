FROM python:3.12-slim

# Install system deps required by neonize (libmagic)
RUN apt-get update && apt-get install -y \
    libmagic1 \
    libmagic-dev \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Create data directories
RUN mkdir -p data/raw data/processed data/faiss data/eval

EXPOSE 8000

CMD uvicorn app.api.main:app --host 0.0.0.0 --port ${PORT:-8000}

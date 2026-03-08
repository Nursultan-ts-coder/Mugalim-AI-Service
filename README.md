# RAG Project Starter

This project provides an end-to-end RAG pipeline using LangChain and Google AI Studio.

## Setup

1. Copy `.env.example` to `.env` and add your `GOOGLE_API_KEY`.
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   pip install -r requirements-dev.txt
   ```

## Ingest and Index

Put files in `data/raw/`, then run:

```bash
python -m app.cli ingest
```

## Query

```bash
python -m app.cli query "What is in the knowledge base?"
```

## API

```bash
uvicorn app.api:app --reload
```

POST `/query` with:

```json
{ "question": "Your question" }
```

## WhatsApp Bot (Neonize)

Install dependencies (includes `neonize`):

```bash
pip install -r requirements.txt
```

Run the bot:

```bash
python -m app.cli whatsapp-bot
```

On first run, scan the QR code printed by Neonize to link your WhatsApp account.
Then send a message to the linked account/device; each message is answered using the same RAG pipeline as the CLI/API.

Optional flags:

```bash
python -m app.cli whatsapp-bot --session-name rag_whatsapp_bot --database data/neonize.db
```

## Evaluation

Create `data/eval/questions.jsonl` with one JSON per line:

```json
{ "question": "Q1", "expected": "optional" }
```

Run:

```bash
python -m app.cli eval
```

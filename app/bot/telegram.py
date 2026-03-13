from __future__ import annotations

import io
import os
import logging
import requests

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

from aiogram import Bot, Dispatcher, F
from aiogram.filters import Command
from aiogram.types import Message

logger = logging.getLogger(__name__)

SUPPORTED_EXTENSIONS = {".pdf", ".docx", ".doc", ".txt", ".html"}


def _call_api(endpoint: str, method: str = "GET", **kwargs) -> dict:
    api_url = os.getenv("API_URL", "http://localhost:8000").rstrip("/")
    url = f"{api_url}{endpoint}"
    try:
        if method == "GET":
            response = requests.get(url, timeout=30, **kwargs)
        else:
            response = requests.post(url, timeout=30, **kwargs)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.ConnectionError:
        return {"status": "error", "message": "API server is not running"}
    except requests.exceptions.Timeout:
        return {"status": "error", "message": "API request timed out"}
    except Exception as e:
        return {"status": "error", "message": str(e)}


async def cmd_start(message: Message) -> None:
    await message.answer(
        "🤖 RAG Telegram Bot\n\n"
        "Commands:\n"
        "/help - Show this message\n"
        "/ping - Health check\n"
        "/status - Show indexed files count\n"
        "/ingest - Re-index documents\n\n"
        "📎 Send a file (PDF, DOCX, TXT, HTML) to upload it.\n"
        "📝 Send any question and I will answer using the knowledge base."
    )


async def cmd_ping(message: Message) -> None:
    await message.answer("🏓 pong ✅")


async def cmd_status(message: Message) -> None:
    response = _call_api("/status")
    if response.get("status") == "error":
        await message.answer(f"❌ API Error: {response.get('message')}")
    else:
        chunks = response.get("chunks_indexed", 0)
        files = response.get("uploaded_files", 0)
        await message.answer(
            f"📊 Knowledge Base Status:\n\n"
            f"📁 Uploaded files: {files}\n"
            f"📚 Indexed chunks: {chunks}"
        )


async def cmd_ingest(message: Message) -> None:
    await message.answer("⏳ Indexing files...")
    response = _call_api("/ingest", method="POST")
    if response.get("status") == "error":
        await message.answer(f"❌ Ingestion failed: {response.get('message')}")
    else:
        chunks = response.get("chunks_indexed", 0)
        await message.answer(f"✅ Indexing complete!\n📚 Indexed {chunks} chunks")


async def handle_document(message: Message, bot: Bot) -> None:
    doc = message.document
    if doc is None:
        return

    filename = doc.file_name or "unknown"
    ext = os.path.splitext(filename)[1].lower()

    if ext not in SUPPORTED_EXTENSIONS:
        await message.answer(
            f"❌ Unsupported file type: `{ext}`\n"
            f"Supported: {', '.join(SUPPORTED_EXTENSIONS)}"
        )
        return

    await message.answer(f"⏳ Uploading {filename}...")

    file = await bot.get_file(doc.file_id)
    buffer = io.BytesIO()
    await bot.download_file(file.file_path, destination=buffer)
    buffer.seek(0)

    response = _call_api(
        "/upload",
        method="POST",
        files={"file": (filename, buffer, "application/octet-stream")},
    )

    if response.get("status") == "error":
        await message.answer(f"❌ Upload failed: {response.get('message')}")
        return

    await message.answer(
        f"✅ {filename} uploaded!\n\n"
        f"Run /ingest to index it into the knowledge base."
    )


async def handle_question(message: Message) -> None:
    from app.rag.pipelines.query import answer_question

    text = message.text or ""
    if not text:
        return

    try:
        answer, docs = answer_question(text)
        reply = answer.strip()
        if len(reply) > 4000:
            reply = reply[:3999] + "…"
        if docs:
            reply += f"\n\n📚 Sources: {len(docs)} document(s)"
        await message.answer(reply)
    except Exception as e:
        await message.answer(f"❌ Error: {e}")


def run_telegram_bot() -> None:
    import asyncio

    token = os.getenv("TELEGRAM_BOT_TOKEN")
    if not token:
        raise RuntimeError("TELEGRAM_BOT_TOKEN environment variable is not set")

    bot = Bot(token=token)
    dp = Dispatcher()

    dp.message.register(cmd_start, Command(commands=["start", "help"]))
    dp.message.register(cmd_ping, Command(commands=["ping"]))
    dp.message.register(cmd_status, Command(commands=["status"]))
    dp.message.register(cmd_ingest, Command(commands=["ingest"]))
    dp.message.register(handle_document, F.document)
    dp.message.register(handle_question, F.text)

    print("🚀 Starting Telegram bot...")
    asyncio.run(dp.start_polling(bot))

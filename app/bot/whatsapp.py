from __future__ import annotations

import os
from typing import Any
import requests

from app.rag.pipelines.query import answer_question


def _get_attr(obj: Any, *names: str) -> Any:
    current = obj
    for name in names:
        if current is None:
            return None
        current = getattr(current, name, None)
    return current


def _extract_text(event: Any) -> str:
    message = _get_attr(event, "Message") or _get_attr(event, "message")
    if message is None:
        return ""

    text = _get_attr(message, "conversation")
    if text:
        return text.strip()

    text = _get_attr(message, "extended_text_message", "text")
    if text:
        return text.strip()

    text = _get_attr(message, "image_message", "caption")
    if text:
        return text.strip()

    return ""


def _extract_chat_jid(event: Any) -> Any:
    return (
        _get_attr(event, "Info", "MessageSource", "Chat")
        or _get_attr(event, "Info", "message_source", "chat")
        or _get_attr(event, "info", "MessageSource", "Chat")
        or _get_attr(event, "info", "message_source", "chat")
    )


def _build_help_text() -> str:
    return (
        "🤖 RAG WhatsApp Bot\n\n"
        "Commands:\n"
        "/help - Show this message\n"
        "/ping - Health check\n"
        "/status - Show indexed files count\n\n"
        "📝 Usage:\n"
        "Send any question and I will answer using "
        "the indexed knowledge base.\n\n"
        "📄 File Upload:\n"
        "Use the API to upload files:\n"
        "POST http://api.server/upload"
    )


def _format_answer(answer: str, limit: int = 3000) -> str:
    cleaned = answer.strip()
    if len(cleaned) <= limit:
        return cleaned
    return cleaned[: limit - 1].rstrip() + "…"


def _send_text(client_obj: Any, chat_jid: Any, text: str) -> None:
    try:
        client_obj.send_message(chat_jid, text)
    except TypeError:
        client_obj.send_message(chat_jid, text=text)


def _call_api(endpoint: str, method: str = "GET", **kwargs) -> dict:
    api_url = os.getenv("API_URL", "http://localhost:8000").rstrip("/")
    url = f"{api_url}{endpoint}"

    try:
        if method == "GET":
            response = requests.get(url, timeout=30, **kwargs)
        elif method == "POST":
            response = requests.post(url, timeout=30, **kwargs)
        else:
            raise ValueError(f"Unsupported method: {method}")

        response.raise_for_status()
        return response.json()
    except requests.exceptions.ConnectionError:
        return {"status": "error", "message": "API server is not running"}
    except requests.exceptions.Timeout:
        return {"status": "error", "message": "API request timed out"}
    except Exception as e:
        return {"status": "error", "message": str(e)}


def run_whatsapp_bot(session_name: str = "rag_whatsapp_bot", database: str = "data/neonize.db") -> None:
    try:
        from pathlib import Path
        from neonize.client import NewClient
        from neonize.events import ConnectedEv, MessageEv, event
    except ImportError as exc:
        message = str(exc).lower()
        if "libmagic" in message:
            raise RuntimeError(
                "Neonize dependency error: missing system library 'libmagic'. "
                "On macOS run: brew install libmagic"
            ) from exc
        raise RuntimeError(
            "Neonize import failed. Run: pip install -r requirements.txt. "
            f"Original error: {exc}"
        ) from exc

    db_path = Path(database)
    db_path.parent.mkdir(parents=True, exist_ok=True)

    try:
        client = NewClient(name=session_name, database=str(db_path))
    except TypeError as exc:
        if "unexpected keyword argument 'database'" not in str(exc):
            raise
        print(
            "Neonize version does not support custom database path in NewClient; "
            "using default Neonize session storage."
        )
        client = NewClient(session_name)

    @client.event(ConnectedEv)
    def on_connected(_client: Any, _event: Any) -> None:
        print("✅ WhatsApp bot connected")
        print("📱 Commands: /help, /ping, /status")
        print("💬 For file uploads, use the API at http://localhost:8000")

    @client.event(MessageEv)
    def on_message(client_obj: Any, message_event: Any) -> None:
        text = _extract_text(message_event)
        chat_jid = _extract_chat_jid(message_event)

        if chat_jid is None:
            return

        normalized = text.lower().strip() if text else ""

        if normalized in {"/help", "help", "/start"}:
            _send_text(client_obj, chat_jid, _build_help_text())
            return

        if normalized in {"/ping", "ping"}:
            _send_text(client_obj, chat_jid, "🏓 pong ✅")
            return

        if normalized in {"/status", "status"}:
            response = _call_api("/status")
            if response.get("status") == "error":
                _send_text(
                    client_obj,
                    chat_jid,
                    f"❌ API Error: {response.get('message')}\n\n"
                    f"Make sure API server is running:\n"
                    f"uvicorn app.api.main:app --reload"
                )
            else:
                chunks = response.get("chunks_indexed", 0)
                _send_text(
                    client_obj,
                    chat_jid,
                    f"📊 Knowledge Base Status:\n\n"
                    f"📚 Indexed chunks: {chunks}\n\n"
                    f"💡 Upload new files via API at:\n"
                    f"http://localhost:8000/upload"
                )
            return

        if normalized in {"/ingest", "ingest"}:
            _send_text(client_obj, chat_jid, "⏳ Indexing files... (via API)")

            response = _call_api("/ingest", method="POST")
            if response.get("status") == "error":
                _send_text(
                    client_obj,
                    chat_jid,
                    f"❌ Ingestion failed: {response.get('message')}"
                )
            else:
                chunk_count = response.get("chunks_indexed", 0)
                _send_text(
                    client_obj,
                    chat_jid,
                    f"✅ Indexing complete!\n📚 Indexed {chunk_count} chunks"
                )
            return

        if text:
            try:
                answer, docs = answer_question(text)
                response_text = _format_answer(answer)

                if docs:
                    response_text += f"\n\n📚 Sources: {len(docs)} document(s)"

                _send_text(client_obj, chat_jid, response_text)
            except Exception as e:
                _send_text(
                    client_obj,
                    chat_jid,
                    f"🤖 Error: {str(e)}\n\n"
                    f"Try uploading documents via API first:\n"
                    f"POST http://localhost:8000/upload"
                )
            return

    print("🚀 Starting WhatsApp bot...")
    print("📱 If first run, scan the QR code with WhatsApp")
    print("🔗 API Server: http://localhost:8000")
    print("📖 Type /help in WhatsApp for commands\n")
    client.connect()
    event.wait()

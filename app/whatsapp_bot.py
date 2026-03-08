from __future__ import annotations

from pathlib import Path
from typing import Any

from app.pipelines.query import answer_question


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
        "🤖 RAG WhatsApp Bot\n"
        "Send any question and I will answer using your indexed knowledge base.\n\n"
        "Commands:\n"
        "/help - Show this message\n"
        "/ping - Health check"
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


def run_whatsapp_bot(session_name: str = "rag_whatsapp_bot", database: str = "data/neonize.db") -> None:
    try:
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
        print("WhatsApp bot connected. You can start sending messages.")

    @client.event(MessageEv)
    def on_message(client_obj: Any, message_event: Any) -> None:
        text = _extract_text(message_event)
        chat_jid = _extract_chat_jid(message_event)

        if not text or chat_jid is None:
            return

        normalized = text.lower().strip()
        if normalized in {"/help", "help", "/start"}:
            _send_text(client_obj, chat_jid, _build_help_text())
            return

        if normalized in {"/ping", "ping"}:
            _send_text(client_obj, chat_jid, "pong ✅")
            return

        try:
            answer, _docs = answer_question(text)
            _send_text(client_obj, chat_jid, _format_answer(answer))
        except Exception:
            _send_text(
                client_obj,
                chat_jid,
                "I hit an internal error while generating an answer. "
                "Please try again in a moment.",
            )

    print("Starting WhatsApp bot...")
    print("If this is the first run, scan the QR code shown by Neonize.")
    client.connect()
    event.wait()

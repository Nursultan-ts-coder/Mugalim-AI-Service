from pathlib import Path
from typing import List

from langchain_core.documents import Document
from langchain_community.vectorstores import FAISS

from app.config import get_settings
from app.embeddings import get_embeddings


def _index_exists(index_dir: Path) -> bool:
    return (index_dir / "index.faiss").exists()


def build_vectorstore(chunks: List[Document]) -> FAISS:
    settings = get_settings()
    settings.faiss_dir.mkdir(parents=True, exist_ok=True)
    embeddings = get_embeddings()
    store = FAISS.from_documents(chunks, embeddings)
    store.save_local(str(settings.faiss_dir))
    return store


def get_vectorstore() -> FAISS:
    settings = get_settings()
    settings.faiss_dir.mkdir(parents=True, exist_ok=True)
    embeddings = get_embeddings()

    if not _index_exists(settings.faiss_dir):
        raise FileNotFoundError(
            "FAISS index not found. Run `python -m app.cli ingest` first."
        )

    return FAISS.load_local(
        str(settings.faiss_dir),
        embeddings,
        allow_dangerous_deserialization=True,
    )

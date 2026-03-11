from pathlib import Path
from typing import List

from langchain_core.documents import Document
from langchain_community.vectorstores import FAISS

from app.config import get_settings
from app.rag.embeddings import get_embeddings


def _index_exists(index_dir: Path) -> bool:
    return (index_dir / "index.faiss").exists()


def build_vectorstore(chunks: List[Document]) -> FAISS:
    """
    Build or update the FAISS vectorstore.
    If an index exists, merge with it. Otherwise, create a new one.
    """
    settings = get_settings()
    settings.faiss_dir.mkdir(parents=True, exist_ok=True)
    embeddings = get_embeddings()

    new_store = FAISS.from_documents(chunks, embeddings)

    if _index_exists(settings.faiss_dir):
        print(f"📦 Merging with existing index...")
        existing_store = FAISS.load_local(
            str(settings.faiss_dir),
            embeddings,
            allow_dangerous_deserialization=True,
        )
        existing_store.add_documents(chunks)
        existing_store.save_local(str(settings.faiss_dir))
        print(f"✅ Index updated and saved")
        return existing_store
    else:
        print(f"📦 Creating new index...")
        new_store.save_local(str(settings.faiss_dir))
        print(f"✅ Index created and saved")
        return new_store


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

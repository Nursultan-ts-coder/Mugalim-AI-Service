import json
from typing import List

from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter

from app.config import get_settings
from app.loaders import load_documents_from_dir


def ingest_documents() -> List[Document]:
    settings = get_settings()
    documents = load_documents_from_dir(settings.raw_dir)

    splitter = RecursiveCharacterTextSplitter(
        chunk_size=settings.chunk_size,
        chunk_overlap=settings.chunk_overlap,
    )
    chunks = splitter.split_documents(documents)

    settings.processed_dir.mkdir(parents=True, exist_ok=True)
    manifest_path = settings.processed_dir / "chunks.jsonl"
    with manifest_path.open("w", encoding="utf-8") as handle:
        for chunk in chunks:
            record = {
                "content": chunk.page_content,
                "metadata": chunk.metadata,
            }
            handle.write(json.dumps(record, ensure_ascii=True) + "\n")

    return chunks

from typing import List, Optional

from langchain_core.documents import Document

from app.pipelines.ingest import ingest_documents
from app.vectorstore import build_vectorstore


def build_index(chunks: Optional[List[Document]] = None) -> int:
    if chunks is None:
        chunks = ingest_documents()

    if not chunks:
        return 0

    build_vectorstore(chunks)
    return len(chunks)

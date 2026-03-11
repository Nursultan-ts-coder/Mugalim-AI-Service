from pathlib import Path
from typing import Iterable, List

from langchain_core.documents import Document
from langchain_community.document_loaders import (
    BSHTMLLoader,
    Docx2txtLoader,
    PyPDFLoader,
    TextLoader,
)


def _get_loader(path: Path):
    suffix = path.suffix.lower()
    if suffix in {".txt", ".md"}:
        return TextLoader(str(path), encoding="utf-8")
    if suffix == ".pdf":
        return PyPDFLoader(str(path))
    if suffix == ".docx":
        return Docx2txtLoader(str(path))
    if suffix in {".html", ".htm"}:
        return BSHTMLLoader(str(path))
    return None


def load_documents(paths: Iterable[Path]) -> List[Document]:
    documents: List[Document] = []
    for path in paths:
        loader = _get_loader(path)
        if not loader:
            continue
        try:
            documents.extend(loader.load())
        except Exception as exc:
            print(f"Skip {path}: {exc}")
    return documents


def load_documents_from_dir(raw_dir: Path) -> List[Document]:
    if not raw_dir.exists():
        return []
    paths = [path for path in raw_dir.rglob("*") if path.is_file()]
    return load_documents(paths)

import os
from dataclasses import dataclass
from pathlib import Path

try:
    from dotenv import load_dotenv
except ImportError:
    load_dotenv = None


if load_dotenv:
    load_dotenv()


@dataclass(frozen=True)
class Settings:
    base_dir: Path
    data_dir: Path
    raw_dir: Path
    processed_dir: Path
    faiss_dir: Path
    eval_dir: Path
    gen_model: str
    embed_model: str
    temperature: float
    chunk_size: int
    chunk_overlap: int
    retrieval_k: int
    retrieval_fetch_k: int


def get_settings() -> Settings:
    base_dir = Path(__file__).resolve().parents[1]
    data_dir = Path(os.getenv("DATA_DIR", str(base_dir / "data")))

    return Settings(
        base_dir=base_dir,
        data_dir=data_dir,
        raw_dir=Path(os.getenv("RAW_DIR", str(data_dir / "raw"))),
        processed_dir=Path(os.getenv("PROCESSED_DIR", str(data_dir / "processed"))),
        faiss_dir=Path(os.getenv("FAISS_DIR", str(data_dir / "faiss"))),
        eval_dir=Path(os.getenv("EVAL_DIR", str(data_dir / "eval"))),
        gen_model=os.getenv("GOOGLE_GEN_MODEL", "gemini-2.0-flash"),
        embed_model=os.getenv("GOOGLE_EMBED_MODEL", "gemini-embedding-001"),
        temperature=float(os.getenv("TEMPERATURE", "0.2")),
        chunk_size=int(os.getenv("CHUNK_SIZE", "800")),
        chunk_overlap=int(os.getenv("CHUNK_OVERLAP", "120")),
        retrieval_k=int(os.getenv("RETRIEVAL_K", "4")),
        retrieval_fetch_k=int(os.getenv("RETRIEVAL_FETCH_K", "12")),
    )

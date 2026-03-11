from fastapi import FastAPI, File, UploadFile, HTTPException
from pydantic import BaseModel

from app.config import get_settings
from app.rag.pipelines.query import answer_question
from app.rag.pipelines.index import build_index

app = FastAPI(title="RAG API")


class QueryRequest(BaseModel):
    question: str


class QueryResponse(BaseModel):
    answer: str
    sources: list[str]


class UploadResponse(BaseModel):
    file_name: str
    path: str
    message: str


@app.get("/health")
def health():
    return {"status": "ok"}


@app.get("/status")
def get_status():
    try:
        settings = get_settings()
        processed_path = settings.processed_dir / "chunks.jsonl"

        chunks_count = 0
        if processed_path.exists():
            chunks_count = sum(1 for _ in processed_path.open())

        raw_files = list(settings.raw_dir.glob("*")) if settings.raw_dir.exists() else []

        return {
            "status": "ok",
            "chunks_indexed": chunks_count,
            "uploaded_files": len(raw_files),
            "message": "Knowledge base status retrieved successfully"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Status check failed: {str(e)}")


@app.post("/query", response_model=QueryResponse)
def query(req: QueryRequest):
    answer, docs = answer_question(req.question)
    sources = [doc.metadata.get("source", "unknown") for doc in docs]
    return QueryResponse(answer=answer, sources=sources)


@app.post("/upload", response_model=UploadResponse)
async def upload_file(file: UploadFile = File(...)):
    try:
        settings = get_settings()
        settings.raw_dir.mkdir(parents=True, exist_ok=True)

        file_path = settings.raw_dir / (file.filename or "unknown")
        content = await file.read()

        with open(file_path, "wb") as f:
            f.write(content)

        return UploadResponse(
            file_name=file.filename or "unknown",
            path=str(file_path),
            message=f"✅ File uploaded to {file_path}",
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Upload failed: {str(e)}")


@app.post("/ingest")
async def ingest_files():
    try:
        chunk_count = build_index()
        return {
            "status": "success",
            "chunks_indexed": chunk_count,
            "message": f"✅ Indexed {chunk_count} chunks from local files"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ingestion failed: {str(e)}")

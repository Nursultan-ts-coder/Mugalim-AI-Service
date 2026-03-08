from fastapi import FastAPI
from pydantic import BaseModel

from app.pipelines.query import answer_question

app = FastAPI(title="RAG API")


class QueryRequest(BaseModel):
    question: str


class QueryResponse(BaseModel):
    answer: str
    sources: list[str]


@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/query", response_model=QueryResponse)
def query(req: QueryRequest):
    answer, docs = answer_question(req.question)
    sources = [doc.metadata.get("source", "unknown") for doc in docs]
    return QueryResponse(answer=answer, sources=sources)

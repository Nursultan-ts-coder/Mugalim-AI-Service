from langchain_google_genai import GoogleGenerativeAIEmbeddings

from app.config import get_settings


def get_embeddings() -> GoogleGenerativeAIEmbeddings:
    settings = get_settings()
    return GoogleGenerativeAIEmbeddings(model=settings.embed_model)

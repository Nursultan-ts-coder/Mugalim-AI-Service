from langchain_google_genai import ChatGoogleGenerativeAI

from app.config import get_settings


def get_llm() -> ChatGoogleGenerativeAI:
    settings = get_settings()
    return ChatGoogleGenerativeAI(
        model=settings.gen_model,
        temperature=settings.temperature,
    )

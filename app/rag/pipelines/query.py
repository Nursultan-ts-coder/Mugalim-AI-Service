from typing import List, Tuple

from langchain_core.documents import Document
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate

from app.config import get_settings
from app.rag.llm import get_llm
from app.rag.vectorstore import get_vectorstore


def _format_context(docs: List[Document]) -> str:
    parts = []
    for index, doc in enumerate(docs, start=1):
        source = doc.metadata.get("source", "unknown")
        parts.append(f"[{index}] {source}\n{doc.page_content}")
    return "\n\n".join(parts)


def retrieve_documents(question: str) -> List[Document]:
    settings = get_settings()
    store = get_vectorstore()

    docs = store.max_marginal_relevance_search(
        question,
        k=settings.retrieval_k,
        fetch_k=settings.retrieval_fetch_k,
    )
    return docs


def answer_question(question: str) -> Tuple[str, List[Document]]:
    docs = retrieve_documents(question)
    context = _format_context(docs)

    prompt = ChatPromptTemplate.from_messages(
        [
            (
                "system",
                "You are a friendly and helpful assistant. "
                "Answer the user's question in a clear, conversational, and natural tone. "
                "Use the provided context as your knowledge source. "
                "Format your response with bullet points or numbered lists when it improves clarity. "
                "Keep answers concise but complete — avoid dumping raw text. "
                "If the context does not contain enough information to answer, politely say so "
                "and suggest the user upload more relevant documents.",
            ),
            ("human", "Question: {question}\n\nContext:\n{context}"),
        ]
    )

    chain = prompt | get_llm() | StrOutputParser()
    response = chain.invoke({"question": question, "context": context})
    return response, docs

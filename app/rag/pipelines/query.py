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
                "Answer using only the provided context. If the context is missing, "
                "say you do not know.",
            ),
            ("human", "Question: {question}\n\nContext:\n{context}"),
        ]
    )

    chain = prompt | get_llm() | StrOutputParser()
    response = chain.invoke({"question": question, "context": context})
    return response, docs

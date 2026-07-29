"""
OWNER: Person 3 (Single RAG) & Person 5 (Multi-Turn RAG)

Retrieves relevant PubMed chunks from ChromaDB.
"""
from langchain_chroma import Chroma
from langchain_groq import ChatGroq
from langchain_core.messages import HumanMessage
from langsmith import traceable
from app.models.schemas import RetrievedChunk, Message
from app.config import get_settings


@traceable(name="retrieve", tags=["rag", "retrieval"])
def retrieve(query: str, vector_store: Chroma, top_k: int = 5) -> list[RetrievedChunk]:
    """
    Similarity search against the ChromaDB collection.
    Returns up to `top_k` chunks sorted by relevance score (descending).
    """
    results = vector_store.similarity_search_with_relevance_scores(query, k=top_k)
    chunks = []
    for doc, score in results:
        chunks.append(RetrievedChunk(
            content=doc.page_content,
            source=doc.metadata.get("pmid", "unknown"),
            score=round(score, 4),
        ))
    chunks.sort(key=lambda c: c.score, reverse=True)
    return chunks


def format_context(chunks: list[RetrievedChunk]) -> str:
    """
    Format retrieved chunks into a single context string to pass to the LLM.
    """
    parts = [f"[Source: {c.source}]\n{c.content}" for c in chunks]
    return "\n\n---\n\n".join(parts)


@traceable(name="condense-query-s3", tags=["s3", "query-rewrite"])
def condense_query_s3(query: str, history: list[Message]) -> str:
    """
    S3 — Rewrite the follow-up into a self-contained question for the LLM.
    Resolves all pronoun and implicit references from recent history.
    Returns the original query unchanged if history is empty.
    """
    if not history:
        return query

    settings = get_settings()
    llm = ChatGroq(model=settings.groq_model, temperature=0.0, api_key=settings.groq_api_key)

    history_text = "\n".join(f"{m.role.capitalize()}: {m.content}" for m in history)
    prompt = (
        "Given the recent conversation history below and a follow-up question, "
        "rewrite the follow-up as a single, self-contained question that can be answered "
        "without any additional context. Resolve all pronouns and implicit references "
        "using the history. Output only the rewritten question.\n\n"
        f"Recent conversation:\n{history_text}\n\n"
        f"Follow-up question: {query}\n\n"
        "Standalone question:"
    )

    response = llm.invoke([HumanMessage(content=prompt)])
    return response.content.strip()


@traceable(name="condense-query-s4", tags=["s4", "rag", "query-rewrite"])
def condense_query_s4(query: str, history: list[Message]) -> str:
    """
    S4 — Rewrite the follow-up into a standalone question optimised for medical literature search.
    Includes specific medical terms, drug names, and conditions from recent history.
    Returns the original query unchanged if history is empty.
    """
    if not history:
        return query

    settings = get_settings()
    llm = ChatGroq(model=settings.groq_model, temperature=0.0, api_key=settings.groq_api_key)

    history_text = "\n".join(f"{m.role.capitalize()}: {m.content}" for m in history)
    prompt = (
        "Given the recent conversation history below and a follow-up question, "
        "rewrite the follow-up as a single, standalone question optimised for medical "
        "literature search. Include specific medical terms, drug names, conditions, or "
        "treatments referenced in the history. Output only the rewritten question.\n\n"
        f"Recent conversation:\n{history_text}\n\n"
        f"Follow-up question: {query}\n\n"
        "Standalone question:"
    )

    response = llm.invoke([HumanMessage(content=prompt)])
    return response.content.strip()


def retrieve_with_history(
    query: str,
    history: list[Message],
    vector_store: Chroma,
    top_k: int = 5,
) -> list[RetrievedChunk]:
    """
    S4 variant — condenses multi-turn history into a standalone query before retrieval.
    """
    standalone_query = condense_query_s4(query, history)
    return retrieve(standalone_query, vector_store, top_k)

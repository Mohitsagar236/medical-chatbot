"""
Pipeline wrappers for LangSmith tracing.

Each function wraps one full strategy pipeline under a single @traceable root,
so all sub-calls (condense, retrieve, LLM) appear as nested child runs.
"""
from langchain_chroma import Chroma
from langsmith import traceable

from app.models.schemas import Message
from app.config import get_settings
from app.services import rag_service, llm_service


@traceable(name="S2-pipeline", run_type="chain", tags=["strategy:S2", "rag"])
def run_s2(query: str, vector_store: Chroma, top_k: int) -> dict:
    """S2: retrieve → generate."""
    chunks = rag_service.retrieve(query, vector_store, top_k)
    context = rag_service.format_context(chunks)
    result = llm_service.ask_with_context(query, context)
    return {**result, "chunks": chunks}


@traceable(name="S3-pipeline", run_type="chain", tags=["strategy:S3", "multi-turn"])
def run_s3(query: str, history: list[Message]) -> dict:
    """S3: condense query using recent history → LLM call with condensed query only."""
    settings = get_settings()
    window = settings.condense_window
    recent = history[-window:] if len(history) > window else history

    condensed = rag_service.condense_query_s3(query, recent)
    result = llm_service.ask_multi_turn(condensed, [])
    return {**result, "condensed_query": condensed}


@traceable(name="S4-pipeline", run_type="chain", tags=["strategy:S4", "multi-turn", "rag"])
def run_s4(query: str, history: list[Message], vector_store: Chroma, top_k: int) -> dict:
    """S4: condense query → retrieve → generate with condensed query + context."""
    settings = get_settings()
    window = settings.condense_window
    recent = history[-window:] if len(history) > window else history

    condensed = rag_service.condense_query_s4(query, recent)
    chunks = rag_service.retrieve(condensed, vector_store, top_k)
    context = rag_service.format_context(chunks)
    result = llm_service.ask_multi_turn_with_context(condensed, history, context)
    return {**result, "chunks": chunks}

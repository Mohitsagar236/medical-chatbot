"""
LLM service — stubs for integration.

Owners:
  Person 2  →  ask_single
  Person 3  →  ask_with_context
  Person 4  →  ask_multi_turn
  Person 5  →  ask_multi_turn_with_context

All functions return a plain dict so routers can map to their response schemas.
"""
from langchain_groq import ChatGroq
from langchain_core.messages import SystemMessage, HumanMessage, AIMessage
from langsmith import traceable

from app.models.schemas import Message
from app.config import get_settings

# Shared system prompt used across all four strategies (S1–S4).
MEDICAL_SYSTEM_PROMPT = (
    "You are a knowledgeable medical assistant. "
    "Answer questions accurately and concisely using established medical knowledge. "
    "If you are unsure or the question is outside your knowledge, say so clearly."
)


def _get_llm() -> ChatGroq:
    settings = get_settings()
    return ChatGroq(
        model=settings.groq_model,
        temperature=settings.temperature,
        api_key=settings.groq_api_key,
    )


@traceable(name="S1-single-llm", tags=["strategy:S1"])
def ask_single(query: str) -> dict:
    """S1: bare LLM call, no history, no context."""
    llm = _get_llm()
    messages = [
        SystemMessage(content=MEDICAL_SYSTEM_PROMPT),
        HumanMessage(content=query),
    ]
    response = llm.invoke(messages)
    usage = response.response_metadata.get("token_usage", {})
    return {
        "answer": response.content,
        "model": llm.model_name,
        "prompt_tokens": usage.get("prompt_tokens"),
        "completion_tokens": usage.get("completion_tokens"),
    }


@traceable(name="S2-single-rag", tags=["strategy:S2"])
def ask_with_context(query: str, context: str) -> dict:
    """S2: LLM call augmented with retrieved PubMed context string."""
    llm = _get_llm()

    system = SystemMessage(content=(
        "You are a helpful medical assistant. "
        "Answer the user's question using only the PubMed context provided. "
        "If the context does not contain enough information, say so. "
        "Be concise and cite the source PMIDs when relevant.\n\n"
        f"Context from PubMed:\n{context}"
    ))

    messages = [system, HumanMessage(content=query)]
    response = llm.invoke(messages)
    usage = response.response_metadata.get("token_usage", {})

    return {
        "answer": response.content,
        "model": llm.model_name,
        "prompt_tokens": usage.get("prompt_tokens"),
        "completion_tokens": usage.get("completion_tokens"),
    }


@traceable(name="S3-multi-turn-llm", tags=["strategy:S3", "multi-turn"])
def ask_multi_turn(query: str, history: list[Message]) -> dict:
    """
    S3: LLM call with full conversation history, no retrieval.

    Builds the message list as:
        [system prompt] + [previous turns from history] + [current user query]
    """
    llm = _get_llm()

    messages = [SystemMessage(content=MEDICAL_SYSTEM_PROMPT)]
    for msg in history:
        if msg.role == "user":
            messages.append(HumanMessage(content=msg.content))
        else:
            messages.append(AIMessage(content=msg.content))
    messages.append(HumanMessage(content=query))

    response = llm.invoke(messages)
    usage = response.response_metadata.get("token_usage", {})

    return {
        "answer": response.content,
        "model": llm.model_name,
        "prompt_tokens": usage.get("prompt_tokens"),
        "completion_tokens": usage.get("completion_tokens"),
    }


@traceable(name="S4-multi-turn-rag", tags=["strategy:S4", "multi-turn"])
def ask_multi_turn_with_context(query: str, history: list[Message], context: str) -> dict:
    """S4: LLM call with conversation history + retrieved PubMed context."""
    llm = _get_llm()

    system = SystemMessage(content=(
        "You are a helpful medical assistant. "
        "Answer the user's question using only the PubMed context provided. "
        "If the context does not contain enough information, say so. "
        "Be concise and cite the source PMIDs when relevant.\n\n"
        f"Context from PubMed:\n{context}"
    ))

    messages = [system]
    for m in history:
        if m.role == "user":
            messages.append(HumanMessage(content=m.content))
        else:
            messages.append(AIMessage(content=m.content))
    messages.append(HumanMessage(content=query))

    response = llm.invoke(messages)
    usage = response.response_metadata.get("token_usage", {})

    return {
        "answer": response.content,
        "model": llm.model_name,
        "prompt_tokens": usage.get("prompt_tokens"),
        "completion_tokens": usage.get("completion_tokens"),
    }

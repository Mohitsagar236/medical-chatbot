"""
S5 — Agentic RAG

A LangGraph ReAct agent that decides when and how many times to search
ChromaDB, rather than always retrieving exactly once like S2.

The agent loop:
  1. Receives the user query
  2. Decides: do I need to search PubMed, or do I already know enough?
  3. Calls search_pubmed(query) tool — may call it multiple times with
     different queries if first results are insufficient
  4. When satisfied, produces a final grounded answer

Token counts are summed across all LLM calls in the agent loop so the
cost metric in evaluation reflects the true cost of the full run.
"""
from langchain_groq import ChatGroq
from langchain_core.messages import SystemMessage, HumanMessage, AIMessage
from langchain_core.tools import tool
from langsmith import traceable
from langgraph.prebuilt import create_react_agent

from app.config import get_settings
from app.models.schemas import RetrievedChunk, ToolCallLog
from app.services import rag_service


AGENT_SYSTEM_PROMPT = (
    "You are a medical research assistant with access to a PubMed literature database. "
    "When answering medical questions, use the search_pubmed tool to retrieve relevant "
    "abstracts before responding. You may call search_pubmed multiple times with different "
    "queries if the first search does not return sufficient information. "
    "Always ground your final answer in the retrieved literature and cite PMIDs when relevant. "
    "If retrieved context does not contain enough information to answer confidently, say so clearly."
)


def _make_search_tool(vector_store, top_k: int, all_chunks: list, tool_calls_log: list):
    """
    Factory that creates the search_pubmed tool as a closure over mutable
    containers, so the router can inspect what the agent retrieved after the run.
    """
    @tool
    def search_pubmed(query: str) -> str:
        """
        Search the PubMed medical literature database for abstracts relevant
        to a medical topic, condition, treatment, or drug. Returns formatted
        context from the most semantically similar abstracts.
        """
        chunks = rag_service.retrieve(query, vector_store, top_k)
        all_chunks.extend(chunks)
        tool_calls_log.append(ToolCallLog(query=query, chunks_found=len(chunks)))
        if not chunks:
            return "No relevant PubMed abstracts found for this query."
        return rag_service.format_context(chunks)

    return search_pubmed


@traceable(name="S5-agent-rag", run_type="chain", tags=["strategy:S5", "agent", "rag"])
def run_agent(query: str, vector_store, top_k: int = 5) -> dict:
    """
    S5: ReAct agent with dynamic PubMed retrieval.
    Returns answer, all retrieved chunks, tool call log, and total token counts.
    """
    settings = get_settings()
    llm = ChatGroq(
        model=settings.groq_model,
        temperature=settings.temperature,
        api_key=settings.groq_api_key,
    )

    all_chunks: list[RetrievedChunk] = []
    tool_calls_log: list[ToolCallLog] = []

    search_tool = _make_search_tool(vector_store, top_k, all_chunks, tool_calls_log)

    agent = create_react_agent(
        llm,
        tools=[search_tool],
        prompt=SystemMessage(content=AGENT_SYSTEM_PROMPT),
    )

    result = agent.invoke(
        {"messages": [HumanMessage(content=query)]},
        config={"recursion_limit": 10},  # caps at ~4 tool calls max
    )

    # Sum token usage across every LLM call in the agent loop
    total_prompt = 0
    total_completion = 0
    for msg in result["messages"]:
        if isinstance(msg, AIMessage):
            usage = msg.response_metadata.get("token_usage", {})
            total_prompt += usage.get("prompt_tokens", 0)
            total_completion += usage.get("completion_tokens", 0)

    final_answer = result["messages"][-1].content

    return {
        "answer": final_answer,
        "model": settings.groq_model,
        "tool_calls": tool_calls_log,
        "retrieved_chunks": all_chunks,
        "prompt_tokens": total_prompt or None,
        "completion_tokens": total_completion or None,
    }

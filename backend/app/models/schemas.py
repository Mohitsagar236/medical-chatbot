"""
Shared Pydantic request/response schemas for all four strategies.
"""
from pydantic import BaseModel, Field
from typing import Literal


# ---------------------------------------------------------------------------
# Shared
# ---------------------------------------------------------------------------

class Message(BaseModel):
    role: Literal["user", "assistant"]
    content: str


# ---------------------------------------------------------------------------
# S1 – Single LLM  (no RAG, no memory)
# ---------------------------------------------------------------------------

class SingleLLMRequest(BaseModel):
    query: str = Field(..., min_length=1, description="Medical question")


class SingleLLMResponse(BaseModel):
    answer: str
    strategy: Literal["S1-single-llm"] = "S1-single-llm"
    model: str
    prompt_tokens: int | None = None
    completion_tokens: int | None = None


# ---------------------------------------------------------------------------
# S2 – Single RAG  (RAG, no memory)
# ---------------------------------------------------------------------------

class SingleRAGRequest(BaseModel):
    query: str = Field(..., min_length=1)
    top_k: int = Field(default=5, ge=1, le=20, description="Number of PubMed chunks to retrieve")


class RetrievedChunk(BaseModel):
    content: str
    source: str          # e.g., PubMed ID
    score: float


class SingleRAGResponse(BaseModel):
    answer: str
    strategy: Literal["S2-single-rag"] = "S2-single-rag"
    retrieved_chunks: list[RetrievedChunk]
    model: str
    prompt_tokens: int | None = None
    completion_tokens: int | None = None


# ---------------------------------------------------------------------------
# S3 – Multi-Turn LLM  (no RAG, with memory)
# ---------------------------------------------------------------------------

class MultiTurnLLMRequest(BaseModel):
    session_id: str = Field(..., description="Client-generated UUID for the conversation session")
    query: str = Field(..., min_length=1)


class MultiTurnLLMResponse(BaseModel):
    answer: str
    strategy: Literal["S3-multi-turn-llm"] = "S3-multi-turn-llm"
    model: str | None = None
    prompt_tokens: int | None = None
    completion_tokens: int | None = None
    session_id: str
    history_length: int        # number of turns retained


# ---------------------------------------------------------------------------
# S4 – Multi-Turn RAG  (RAG + memory)
# ---------------------------------------------------------------------------

class MultiTurnRAGRequest(BaseModel):
    session_id: str = Field(..., description="Client-generated UUID for the conversation session")
    query: str = Field(..., min_length=1)
    top_k: int = Field(default=5, ge=1, le=20)


class MultiTurnRAGResponse(BaseModel):
    answer: str
    strategy: Literal["S4-multi-turn-rag"] = "S4-multi-turn-rag"
    session_id: str
    retrieved_chunks: list[RetrievedChunk]
    history_length: int
    prompt_tokens: int | None = None
    completion_tokens: int | None = None


# ---------------------------------------------------------------------------
# S5 – Agent RAG  (agentic tool-use, dynamic retrieval)
# ---------------------------------------------------------------------------

class ToolCallLog(BaseModel):
    query: str
    chunks_found: int


class AgentRAGRequest(BaseModel):
    query: str = Field(..., min_length=1)
    top_k: int = Field(default=5, ge=1, le=20)


class AgentRAGResponse(BaseModel):
    answer: str
    strategy: Literal["S5-agent-rag"] = "S5-agent-rag"
    tool_calls: list[ToolCallLog]
    retrieved_chunks: list[RetrievedChunk]
    model: str
    prompt_tokens: int | None = None
    completion_tokens: int | None = None


# ---------------------------------------------------------------------------
# Ingestion
# ---------------------------------------------------------------------------

class IngestionRequest(BaseModel):
    query: str = Field(..., description="PubMed search query, e.g. 'diabetes mellitus treatment'")
    max_results: int = Field(default=100, ge=1, le=1000)


class IngestionResponse(BaseModel):
    status: Literal["started", "completed", "failed"]
    documents_ingested: int
    message: str


class IngestionStatusResponse(BaseModel):
    collection: str
    document_count: int
    embedding_model: str
    seed_status: str        # idle | seeding | ready | error
    seed_message: str
    queries_done: int
    total_queries: int

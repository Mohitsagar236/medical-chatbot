"""
S5 — Agent RAG  (agentic tool-use, dynamic retrieval)
Routes: /api/v1/chat/agent-rag/...
"""
from fastapi import APIRouter, Depends, HTTPException
from langchain_chroma import Chroma

from app.models.schemas import AgentRAGRequest, AgentRAGResponse
from app.services.agent_service import run_agent
from app.core.vector_store import get_vector_store

router = APIRouter(prefix="/chat/agent-rag", tags=["S5 — Agent RAG"])


@router.post("/", response_model=AgentRAGResponse)
def agent_rag(body: AgentRAGRequest, vector_store: Chroma = Depends(get_vector_store)):
    """
    ReAct agent that dynamically decides when and how many times to search
    PubMed before answering. Unlike S2, retrieval is not hardcoded — the
    agent chooses its own queries and search count based on the question.
    """
    try:
        result = run_agent(body.query, vector_store, body.top_k)
        return AgentRAGResponse(**result)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))

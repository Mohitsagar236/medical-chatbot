"""
S4 — Multi-Turn RAG  (RAG + memory) — Person 5
Routes: /api/v1/chat/multi-turn-rag/...
"""
from fastapi import APIRouter, Depends, HTTPException
from langchain_chroma import Chroma

from app.models.schemas import MultiTurnRAGRequest, MultiTurnRAGResponse
from app.services.pipeline_service import run_s4
from app.services.conversation_store import get_history, append_turn, clear_session, session_length
from app.core.vector_store import get_vector_store

router = APIRouter(prefix="/chat/multi-turn-rag", tags=["S4 — Multi-Turn RAG"])


@router.post("/", response_model=MultiTurnRAGResponse)
def multi_turn_rag(body: MultiTurnRAGRequest, vector_store: Chroma = Depends(get_vector_store)):
    """Retrieve PubMed context, then answer using full conversation history + context."""
    try:
        history = get_history(body.session_id)
        result = run_s4(body.query, history, vector_store, body.top_k)
        chunks = result.pop("chunks")
        append_turn(body.session_id, body.query, result["answer"])
        return MultiTurnRAGResponse(
            **result,
            session_id=body.session_id,
            retrieved_chunks=chunks,
            history_length=session_length(body.session_id),
        )
    except NotImplementedError:
        raise HTTPException(status_code=501, detail="S4 not yet implemented.")
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))


@router.delete("/{session_id}", status_code=204)
def clear_multi_turn_rag_session(session_id: str):
    """Clear conversation history for a session."""
    clear_session(session_id)

"""
S3 — Multi-Turn LLM  (no RAG, with memory) — Person 4
Routes: /api/v1/chat/multi-turn-llm/...
"""
from fastapi import APIRouter, HTTPException

from app.models.schemas import MultiTurnLLMRequest, MultiTurnLLMResponse
from app.services.pipeline_service import run_s3
from app.services.conversation_store import get_history, append_turn, clear_session, session_length

router = APIRouter(prefix="/chat/multi-turn-llm", tags=["S3 — Multi-Turn LLM"])


@router.post("/", response_model=MultiTurnLLMResponse)
def multi_turn_llm(body: MultiTurnLLMRequest):
    """Condense query using recent history, then answer — no retrieval."""
    try:
        history = get_history(body.session_id)
        result = run_s3(body.query, history)
        condensed_query = result.pop("condensed_query")
        append_turn(body.session_id, condensed_query, result["answer"])
        return MultiTurnLLMResponse(
            **result,
            session_id=body.session_id,
            history_length=session_length(body.session_id),
        )
    except NotImplementedError:
        raise HTTPException(status_code=501, detail="S3 not yet implemented.")
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))


@router.delete("/{session_id}", status_code=204)
def clear_multi_turn_llm_session(session_id: str):
    """Clear conversation history for a session."""
    clear_session(session_id)

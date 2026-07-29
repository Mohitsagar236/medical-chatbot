"""
S1 — Single LLM  (no RAG, no memory) — Person 2
Routes: /api/v1/chat/single-llm/...
"""
from fastapi import APIRouter, HTTPException

from app.models.schemas import SingleLLMRequest, SingleLLMResponse
from app.services import llm_service

router = APIRouter(prefix="/chat/single-llm", tags=["S1 — Single LLM"])


@router.post("/", response_model=SingleLLMResponse)
def single_llm(body: SingleLLMRequest):
    """Answer a medical question with a bare LLM call — no retrieval, no history."""
    try:
        result = llm_service.ask_single(body.query)
        return SingleLLMResponse(**result)
    except NotImplementedError:
        raise HTTPException(status_code=501, detail="S1 not yet implemented.")
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))

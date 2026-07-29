"""
S2 — Single RAG  (RAG, no memory) — Person 3
Routes: /api/v1/chat/single-rag/...
"""
from fastapi import APIRouter, Depends, HTTPException
from langchain_chroma import Chroma

from app.models.schemas import SingleRAGRequest, SingleRAGResponse
from app.services.pipeline_service import run_s2
from app.core.vector_store import get_vector_store

router = APIRouter(prefix="/chat/single-rag", tags=["S2 — Single RAG"])


@router.post("/", response_model=SingleRAGResponse)
def single_rag(body: SingleRAGRequest, vector_store: Chroma = Depends(get_vector_store)):
    """Retrieve relevant PubMed chunks, then answer using the LLM with that context."""
    try:
        result = run_s2(body.query, vector_store, body.top_k)
        chunks = result.pop("chunks")
        return SingleRAGResponse(**result, retrieved_chunks=chunks)
    except NotImplementedError:
        raise HTTPException(status_code=501, detail="S2 not yet implemented.")
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))

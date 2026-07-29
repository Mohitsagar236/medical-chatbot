"""
FastAPI dependency re-exports for convenience.
Import from here in routers to keep imports consistent.
"""
from app.core.embeddings import get_embedding_model
from app.core.vector_store import get_vector_store
from app.config import get_settings

__all__ = ["get_embedding_model", "get_vector_store", "get_settings"]

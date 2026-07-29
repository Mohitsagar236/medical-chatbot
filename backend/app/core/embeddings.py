"""
Shared embedding model — all-MiniLM-L6-v2 via ChromaDB's built-in ONNX runtime.
No torch, no Rust deps — onnxruntime is already a chromadb dependency.
Releases the GIL during inference so the async event loop stays responsive.
"""
from functools import lru_cache


class _ChromaEmbedWrapper:
    """Wraps chromadb's DefaultEmbeddingFunction to match LangChain's interface."""

    def __init__(self):
        from chromadb.utils.embedding_functions import DefaultEmbeddingFunction  # lazy
        self._fn = DefaultEmbeddingFunction()

    def embed_documents(self, texts: list[str]) -> list[list[float]]:
        return [emb.tolist() for emb in self._fn(texts)]

    def embed_query(self, text: str) -> list[float]:
        return self._fn([text])[0].tolist()


@lru_cache(maxsize=1)
def get_embedding_model() -> _ChromaEmbedWrapper:
    return _ChromaEmbedWrapper()

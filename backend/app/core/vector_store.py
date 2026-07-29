"""
ChromaDB client — lazy imports so chromadb doesn't load at startup.
Connects to a remote HTTP server when CHROMA_HOST is set,
otherwise falls back to a local persisted directory.
"""
from functools import lru_cache
from app.config import get_settings
from app.core.embeddings import get_embedding_model


@lru_cache(maxsize=1)
def get_vector_store():
    import chromadb                          # lazy — deferred until first call
    from langchain_chroma import Chroma      # lazy — deferred until first call
    settings = get_settings()
    if settings.chroma_host:
        client = chromadb.HttpClient(
            host=settings.chroma_host,
            port=settings.chroma_port,
        )
        return Chroma(
            client=client,
            collection_name=settings.chroma_collection,
            embedding_function=get_embedding_model(),
        )
    return Chroma(
        collection_name=settings.chroma_collection,
        embedding_function=get_embedding_model(),
        persist_directory=settings.chroma_persist_dir,
    )

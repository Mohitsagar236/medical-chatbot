"""
Ingestion service.

Fetches PubMed records for an ad-hoc query, chunks them with the same logic used
by the full seed job, embeds them through the configured Chroma vector store, and
returns the number of chunks newly stored.
"""
import time

from Bio import Entrez
from langchain_chroma import Chroma

from app.services import seeding


def ingest(
    query: str,
    max_results: int,
    vector_store: Chroma,
    email: str,
    ncbi_api_key: str = "",
) -> int:
    """Fetch PubMed records, chunk, embed, and store new chunks in ChromaDB."""
    if not email:
        raise ValueError("PUBMED_EMAIL is required before ingesting PubMed data.")

    Entrez.email = email
    if ncbi_api_key:
        Entrez.api_key = ncbi_api_key

    sleep_s = 0.1 if ncbi_api_key else 0.4
    seeding._state.update({
        "status": "seeding",
        "chunks_stored": vector_store._collection.count(),
        "queries_done": 0,
        "total_queries": 1,
        "message": f"Ingesting PubMed records for '{query}'.",
    })

    try:
        pmids = list(dict.fromkeys(seeding._search(query, max_results)))
        chunks_stored = 0

        for pmid in pmids:
            doc = seeding._fetch_full_text(pmid) or seeding._fetch_abstract(pmid)
            if not doc:
                time.sleep(sleep_s)
                continue

            chunks = seeding._chunk(doc)
            ids = [
                f"{chunk['metadata']['pmid']}_chunk_{chunk['metadata']['chunk_index']}"
                for chunk in chunks
            ]
            existing_ids = set(vector_store._collection.get(ids=ids).get("ids", [])) if ids else set()
            new_chunks = [
                (chunk, chunk_id)
                for chunk, chunk_id in zip(chunks, ids)
                if chunk_id not in existing_ids
            ]

            if new_chunks:
                vector_store.add_texts(
                    texts=[chunk["text"] for chunk, _ in new_chunks],
                    metadatas=[chunk["metadata"] for chunk, _ in new_chunks],
                    ids=[chunk_id for _, chunk_id in new_chunks],
                )
                chunks_stored += len(new_chunks)

            time.sleep(sleep_s)

        total = vector_store._collection.count()
        seeding._state.update({
            "status": "ready",
            "chunks_stored": total,
            "queries_done": 1,
            "message": f"Ingestion complete - {chunks_stored} new chunks stored.",
        })
        return chunks_stored

    except Exception as exc:
        seeding._state.update({
            "status": "error",
            "message": f"Ingestion failed: {exc}",
        })
        raise


def get_collection_count(vector_store: Chroma) -> int:
    """Return total number of documents stored in the collection."""
    return vector_store._collection.count()

import os
import tarfile
import threading
from contextlib import asynccontextmanager

from dotenv import load_dotenv
load_dotenv()  # must run before LangChain imports so LANGCHAIN_TRACING_V2 is set

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.routers import ingestion, single_llm, single_rag, multi_turn_llm, multi_turn_rag, agent_rag
from app.core.vector_store import get_vector_store
from app.config import get_settings
from app.services import seeding


def _restore_from_backup(backup_url: str, chroma_dir: str):
    """Download chroma_db.tar.gz and extract it into place."""
    import requests as req
    tarball = "/tmp/chroma_db.tar.gz"

    seeding._state.update({"status": "seeding", "message": "Downloading DB backup..."})
    with req.get(backup_url, stream=True, timeout=300, allow_redirects=True) as r:
        r.raise_for_status()
        total = int(r.headers.get("content-length", 0))
        downloaded = 0
        with open(tarball, "wb") as f:
            for chunk in r.iter_content(chunk_size=1024 * 1024):  # 1MB chunks
                f.write(chunk)
                downloaded += len(chunk)
                if total:
                    pct = int(downloaded / total * 100)
                    seeding._state["message"] = f"Downloading DB backup... {pct}%"

    seeding._state["message"] = "Extracting DB backup..."
    with tarfile.open(tarball) as tar:
        tar.extractall(path=os.path.dirname(os.path.abspath(chroma_dir)))
    os.remove(tarball)


@asynccontextmanager
async def lifespan(app: FastAPI):
    settings = get_settings()

    def _init():
        vs = get_vector_store()
        if vs._collection.count() > 0:
            seeding._state.update({
                "status": "ready",
                "chunks_stored": vs._collection.count(),
                "message": "DB already populated — skipping seed.",
            })
            return

        if settings.chroma_backup_url:
            # Fast path — restore pre-built DB (~60s) instead of re-seeding (~22h)
            _restore_from_backup(settings.chroma_backup_url, settings.chroma_persist_dir)
            # Reinitialise the vector store from the restored files
            get_vector_store.cache_clear()
            vs = get_vector_store()
            seeding._state.update({
                "status": "ready",
                "chunks_stored": vs._collection.count(),
                "message": f"DB restored from backup — {vs._collection.count()} chunks.",
            })
        elif settings.pubmed_email:
            # Slow path — seed from PubMed (use only when no backup URL is set)
            seeding.run_seed(
                vector_store=vs,
                email=settings.pubmed_email,
                ncbi_api_key=settings.ncbi_api_key,
            )

    threading.Thread(target=_init, daemon=True, name="db-init").start()
    yield


app = FastAPI(
    title="Medical Chatbot Strategy Comparison API",
    description=(
        "CS 540 — Team Pentacle\n\n"
        "Compares four LLM strategies on medical Q&A:\n"
        "S1 Single LLM · S2 Single RAG · S3 Multi-Turn LLM · S4 Multi-Turn RAG"
    ),
    version="0.1.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

API_PREFIX = "/api/v1"

app.include_router(ingestion.router,       prefix=API_PREFIX)
app.include_router(single_llm.router,      prefix=API_PREFIX)
app.include_router(single_rag.router,      prefix=API_PREFIX)
app.include_router(multi_turn_llm.router,  prefix=API_PREFIX)
app.include_router(multi_turn_rag.router,  prefix=API_PREFIX)
app.include_router(agent_rag.router,       prefix=API_PREFIX)


@app.api_route("/health", methods=["GET", "HEAD"], tags=["Health"])
def health():
    return {"status": "ok"}

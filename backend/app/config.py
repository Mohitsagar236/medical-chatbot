from pydantic_settings import BaseSettings, SettingsConfigDict
from functools import lru_cache


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    # LLM
    groq_api_key: str = ""
    groq_model: str = "llama-3.3-70b-versatile"
    temperature: float = 0.0

    # Embeddings — all-MiniLM-L6-v2 via chromadb's built-in ONNX runtime (no torch)
    embedding_model: str = "all-MiniLM-L6-v2"

    # ChromaDB — set chroma_host to use a remote server; leave empty for local disk
    chroma_persist_dir: str = "./chroma_db"
    chroma_collection: str = "pubmed_abstracts"
    chroma_host: str = ""          # e.g. "my-chroma-server.example.com"
    chroma_port: int = 8000
    chroma_backup_url: str = ""    # URL to chroma_db.tar.gz — downloaded on cold start if DB is empty

    # PubMed ingestion
    pubmed_email: str = ""          # required by NCBI Entrez
    pubmed_max_results: int = 500
    ncbi_api_key: str = ""          # optional — raises rate limit from 3 to 10 req/s

    # Multi-turn conversation
    max_history_turns: int = 10     # pairs of (user, assistant) to keep
    condense_window: int = 3        # how many recent turns to pass to the condense LLM call

    # LangSmith tracing
    langsmith_api_key: str = ""
    langchain_tracing_v2: str = "false"
    langchain_project: str = "cs540-medical-chatbot"
    langchain_endpoint: str = "https://api.smith.langchain.com"


@lru_cache
def get_settings() -> Settings:
    return Settings()

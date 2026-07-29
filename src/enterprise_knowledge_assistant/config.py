"""Application configuration read from environment variables."""

from dataclasses import dataclass
import os
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[2]


@dataclass(frozen=True)
class Settings:
    """Runtime settings with safe, local defaults."""

    knowledge_dir: Path = PROJECT_ROOT / "knowledge_base"
    chroma_dir: Path = PROJECT_ROOT / "chroma_db"
    output_dir: Path = PROJECT_ROOT / "output"
    log_dir: Path = PROJECT_ROOT / "logs"
    chat_model: str = os.getenv("OLLAMA_CHAT_MODEL", "gpt-oss:120b-cloud")
    embedding_model: str = os.getenv(
        "OLLAMA_EMBEDDING_MODEL",
        "nomic-embed-text",
    )
    chunk_size: int = int(os.getenv("RAG_CHUNK_SIZE", "500"))
    chunk_overlap: int = int(os.getenv("RAG_CHUNK_OVERLAP", "100"))
    retrieval_k: int = int(os.getenv("RAG_RETRIEVAL_K", "4"))
    score_threshold: float = float(os.getenv("RAG_SCORE_THRESHOLD", "0.70"))
    max_retries: int = int(os.getenv("RAG_MAX_RETRIES", "1"))


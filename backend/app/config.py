"""
Application configuration for FinCheck AI.
Loads settings from environment variables or .env file.
"""

import os
import sys
from pathlib import Path
from pydantic_settings import BaseSettings
from dotenv import load_dotenv

# Ensure project root is in sys.path
ROOT_DIR = Path(__file__).resolve().parent.parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

env_file = ROOT_DIR / ".env"
if env_file.exists():
    load_dotenv(env_file)
else:
    load_dotenv()


class Settings(BaseSettings):
    DATABASE_URL: str = os.getenv("DATABASE_URL", "")
    NVIDIA_API_KEY: str = os.getenv("NVIDIA_API_KEY", "")
    GEMINI_API_KEY: str = os.getenv("GEMINI_API_KEY", "")

    EMBEDDING_MODEL: str = os.getenv("EMBEDDING_MODEL", "nvidia/nemotron-3-embed-1b")
    EMBEDDING_DIM: int = int(os.getenv("EMBEDDING_DIM", "2048"))
    NVIDIA_EMBEDDING_URL: str = os.getenv(
        "NVIDIA_EMBEDDING_URL", "https://integrate.api.nvidia.com/v1/embeddings"
    )

    RERANKING_MODEL: str = os.getenv(
        "RERANKING_MODEL", "nvidia/llama-nemotron-rerank-vl-1b-v2"
    )
    NVIDIA_RERANKING_URL: str = os.getenv(
        "NVIDIA_RERANKING_URL",
        "https://ai.api.nvidia.com/v1/retrieval/nvidia/llama-nemotron-rerank-vl-1b-v2/reranking",
    )
    RERANK_ENABLED: bool = os.getenv("RERANK_ENABLED", "true").lower() in ("true", "1", "yes")
    RETRIEVAL_TOP_K: int = int(os.getenv("RETRIEVAL_TOP_K", "15"))
    FINAL_RERANK_TOP_N: int = int(os.getenv("FINAL_RERANK_TOP_N", "5"))

    # Generation Configuration (Gemini API)
    GEMINI_MODEL: str = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")
    GEMINI_API_URL: str = os.getenv(
        "GEMINI_API_URL", "https://generativelanguage.googleapis.com/v1beta/models"
    )
    GENERATION_TEMPERATURE: float = float(os.getenv("GENERATION_TEMPERATURE", "0.1"))
    GENERATION_MAX_TOKENS: int = int(os.getenv("GENERATION_MAX_TOKENS", "1024"))
    GENERATION_TIMEOUT_SECONDS: float = float(os.getenv("GENERATION_TIMEOUT_SECONDS", "30.0"))

    class Config:
        extra = "ignore"


settings = Settings()

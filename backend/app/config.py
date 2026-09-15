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

    class Config:
        extra = "ignore"


settings = Settings()

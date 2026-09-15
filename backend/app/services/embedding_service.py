"""
NVIDIA NeMo Retriever Embedding Service for FinCheck AI.
Uses nvidia/nemotron-3-embed-1b (2048 dimensions).
Supports input_type='passage' for corpus indexing and input_type='query' for user queries.
Includes batching, retries with exponential backoff, rate limit handling, and strict dimension validation.
"""

import time
from typing import List, Literal, Optional
import httpx
from backend.app.config import settings


class EmbeddingService:
    def __init__(
        self,
        api_key: Optional[str] = None,
        model: Optional[str] = None,
        endpoint: Optional[str] = None,
        expected_dim: Optional[int] = None,
        timeout_seconds: float = 60.0,
        max_retries: int = 5,
        backoff_factor: float = 2.0,
    ):
        self.api_key = api_key or settings.NVIDIA_API_KEY
        self.model = model or settings.EMBEDDING_MODEL
        self.endpoint = endpoint or settings.NVIDIA_EMBEDDING_URL
        self.expected_dim = expected_dim or settings.EMBEDDING_DIM
        self.timeout_seconds = timeout_seconds
        self.max_retries = max_retries
        self.backoff_factor = backoff_factor

    def _validate_config(self):
        if not self.api_key:
            raise ValueError(
                "NVIDIA_API_KEY is not configured. Please add your NVIDIA API key to the .env file."
            )

    def get_embeddings(
        self,
        texts: List[str],
        input_type: Literal["passage", "query"] = "passage",
    ) -> List[List[float]]:
        """
        Generates embeddings for a list of texts.
        input_type must be:
        - 'passage' for document/chunk ingestion
        - 'query' for user questions
        """
        self._validate_config()

        if not texts:
            return []

        # Validate input_type
        if input_type not in ("passage", "query"):
            raise ValueError(
                f"Invalid input_type '{input_type}'. Must be strictly 'passage' or 'query'."
            )

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Accept": "application/json",
            "Content-Type": "application/json",
        }

        payload = {
            "input": texts,
            "model": self.model,
            "input_type": input_type,
            "encoding_format": "float",
            "truncate": "END",
        }

        last_error = None
        for attempt in range(1, self.max_retries + 1):
            try:
                with httpx.Client(timeout=self.timeout_seconds) as client:
                    response = client.post(self.endpoint, headers=headers, json=payload)

                # Rate limiting (HTTP 429) or transient server errors (5xx)
                if response.status_code == 429 or response.status_code >= 500:
                    wait_time = self.backoff_factor ** attempt
                    print(
                        f"[WARNING] NVIDIA API returned status {response.status_code}. "
                        f"Retrying in {wait_time:.1f}s (attempt {attempt}/{self.max_retries})..."
                    )
                    time.sleep(wait_time)
                    continue

                response.raise_for_status()
                data = response.json()

                # Extract and sort by index
                items = data.get("data", [])
                items.sort(key=lambda x: x.get("index", 0))

                embeddings = [item["embedding"] for item in items]

                if len(embeddings) != len(texts):
                    raise ValueError(
                        f"Expected {len(texts)} embeddings from API, received {len(embeddings)}."
                    )

                # Validate dimensions
                for idx, emb in enumerate(embeddings):
                    dim = len(emb)
                    if dim != self.expected_dim:
                        raise ValueError(
                            f"Embedding at index {idx} has invalid dimension {dim}. "
                            f"Expected exactly {self.expected_dim} dimensions."
                        )

                return embeddings

            except httpx.HTTPStatusError as e:
                last_error = e
                wait_time = self.backoff_factor ** attempt
                print(
                    f"[ERROR] HTTP Error {e.response.status_code}: {e.response.text}. "
                    f"Retrying in {wait_time:.1f}s (attempt {attempt}/{self.max_retries})..."
                )
                time.sleep(wait_time)
            except Exception as e:
                last_error = e
                wait_time = self.backoff_factor ** attempt
                print(
                    f"[ERROR] Network/API error: {e}. "
                    f"Retrying in {wait_time:.1f}s (attempt {attempt}/{self.max_retries})..."
                )
                time.sleep(wait_time)

        raise RuntimeError(
            f"Failed to generate embeddings after {self.max_retries} attempts. Last error: {last_error}"
        )

    def get_query_embedding(self, query: str) -> List[float]:
        """Convenience method for embedding a user query with input_type='query'."""
        results = self.get_embeddings([query], input_type="query")
        return results[0]

    def get_passage_embeddings(self, passages: List[str]) -> List[List[float]]:
        """Convenience method for embedding passages with input_type='passage'."""
        return self.get_embeddings(passages, input_type="passage")


# Singleton instance
embedding_service = EmbeddingService()

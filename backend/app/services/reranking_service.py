"""
NVIDIA NeMo Retriever Reranking Service for FinCheck AI.
Uses nvidia/llama-nemotron-rerank-vl-1b-v2 cross-encoder hosted on NVIDIA API.
Reranks candidate text passages by semantic relevance to a user query.
Includes retries with exponential backoff, rate limit handling, sigmoid score calculation,
and strict protection against leaking API keys or secrets.
"""

import logging
import math
import time
from typing import Any, Dict, List, Optional
import httpx
from backend.app.config import settings

logger = logging.getLogger("fincheck.reranking")


class RerankingError(Exception):
    """Base exception for reranker service failures."""
    pass


class RerankingService:
    def __init__(
        self,
        api_key: Optional[str] = None,
        model: Optional[str] = None,
        endpoint: Optional[str] = None,
        timeout_seconds: float = 20.0,
        max_retries: int = 3,
        backoff_factor: float = 2.0,
    ):
        self.api_key = api_key or settings.NVIDIA_API_KEY
        self.model = model or settings.RERANKING_MODEL
        self.endpoint = endpoint or settings.NVIDIA_RERANKING_URL
        self.timeout_seconds = timeout_seconds
        self.max_retries = max_retries
        self.backoff_factor = backoff_factor

    def _validate_config(self):
        if not self.api_key:
            raise RerankingError(
                "NVIDIA_API_KEY is not configured. Please add your NVIDIA API key to the .env file."
            )

    @staticmethod
    def _sigmoid(logit: float) -> float:
        """Converts raw logit to probability in range (0.0, 1.0)."""
        try:
            return 1.0 / (1.0 + math.exp(-logit))
        except OverflowError:
            return 0.0 if logit < 0 else 1.0

    def rerank(
        self,
        query: str,
        passages: List[str],
    ) -> List[Dict[str, Any]]:
        """
        Reranks candidate passages for a query using the NVIDIA Cross-Encoder Reranker.
        
        Args:
            query: User's financial question.
            passages: List of passage text strings to rank.
            
        Returns:
            List of dicts ordered by relevance (highest relevance first):
            [
                {
                    "index": int,        # original index in passages array
                    "logit": float,      # raw model logit score
                    "score": float       # sigmoid probability score [0.0, 1.0]
                },
                ...
            ]
        """
        self._validate_config()

        clean_query = query.strip()
        if not clean_query:
            raise ValueError("Query string cannot be empty.")

        if not passages:
            return []

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Accept": "application/json",
            "Content-Type": "application/json",
        }

        payload = {
            "model": self.model,
            "query": {"text": clean_query},
            "passages": [{"text": p} for p in passages],
            "truncate": "END",
        }

        last_error = None
        for attempt in range(1, self.max_retries + 1):
            try:
                with httpx.Client(timeout=self.timeout_seconds) as client:
                    response = client.post(self.endpoint, headers=headers, json=payload)

                # Rate limiting (HTTP 429) or transient server error (5xx)
                if response.status_code == 429 or response.status_code >= 500:
                    wait_time = self.backoff_factor ** attempt
                    logger.warning(
                        f"NVIDIA Reranking API returned status {response.status_code}. "
                        f"Retrying in {wait_time:.1f}s (attempt {attempt}/{self.max_retries})..."
                    )
                    time.sleep(wait_time)
                    continue

                response.raise_for_status()
                data = response.json()

                rankings_raw = data.get("rankings", [])
                if not rankings_raw:
                    logger.warning("NVIDIA Reranking API returned empty rankings list.")
                    return []

                results = []
                for item in rankings_raw:
                    idx = int(item.get("index", 0))
                    logit = float(item.get("logit", 0.0))
                    prob = self._sigmoid(logit)
                    results.append(
                        {
                            "index": idx,
                            "logit": round(logit, 4),
                            "score": round(prob, 4),
                        }
                    )

                # API already sorts in descending order by logit, but we guarantee sorting:
                results.sort(key=lambda x: x["logit"], reverse=True)
                return results

            except httpx.HTTPStatusError as e:
                last_error = f"HTTP {e.response.status_code}: {e.response.text[:200]}"
                wait_time = self.backoff_factor ** attempt
                logger.warning(
                    f"Reranker HTTP error (attempt {attempt}/{self.max_retries}): {last_error}. Retrying in {wait_time:.1f}s..."
                )
                time.sleep(wait_time)
            except Exception as e:
                last_error = str(e)
                wait_time = self.backoff_factor ** attempt
                logger.warning(
                    f"Reranker connection error (attempt {attempt}/{self.max_retries}): {last_error}. Retrying in {wait_time:.1f}s..."
                )
                time.sleep(wait_time)

        raise RerankingError(
            f"Failed to rerank passages after {self.max_retries} attempts. Last error: {last_error}"
        )


# Global singleton instance
reranking_service = RerankingService()

"""
Gemini Grounded Answer Generation Service for FinCheck AI.
Generates hallucination-free, factual answers strictly grounded in retrieved banking documents.
Uses Google Gemini API via REST with exponential backoff, rate-limit resilience,
strict citation validation, and safe fallback handling.
"""

import logging
import re
import time
from typing import Any, Dict, List, Optional, Set, Tuple
import httpx

from backend.app.config import settings
from backend.app.models.generation import GenerateResponse
from backend.app.models.retrieval import RetrievedChunk

logger = logging.getLogger("fincheck.generation")


class GenerationError(Exception):
    """Base exception for generation service errors."""
    pass


class GenerationConfigError(GenerationError):
    """Raised when Gemini API configuration (e.g. GEMINI_API_KEY) is missing."""
    pass


class GenerationService:
    def __init__(
        self,
        api_key: Optional[str] = None,
        model: Optional[str] = None,
        api_url: Optional[str] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        timeout_seconds: Optional[float] = None,
        max_retries: int = 3,
        backoff_factor: float = 2.0,
    ):
        self.api_key = api_key or settings.GEMINI_API_KEY
        self.model = model or settings.GEMINI_MODEL
        self.api_url = api_url or settings.GEMINI_API_URL
        self.temperature = (
            temperature
            if temperature is not None
            else settings.GENERATION_TEMPERATURE
        )
        self.max_tokens = max_tokens or settings.GENERATION_MAX_TOKENS
        self.timeout_seconds = (
            timeout_seconds or settings.GENERATION_TIMEOUT_SECONDS
        )
        self.max_retries = max_retries
        self.backoff_factor = backoff_factor

    def _validate_config(self):
        """Validates that GEMINI_API_KEY is present."""
        if not self.api_key:
            raise GenerationConfigError(
                "GEMINI_API_KEY is not configured. Please add your Gemini API key to the .env file."
            )

    def build_prompt(
        self, question: str, chunks: List[RetrievedChunk]
    ) -> Tuple[str, str]:
        """
        Builds the strict system instruction and user prompt containing the retrieved context.
        
        Enforces:
        1. Context-only factual answering.
        2. No speculation or hallucination on interest rates, penalties, or compliance dates.
        3. Mandatory [Source N] citations for all assertions.
        4. Prioritizing official Reserve Bank of India (RBI) circulars as binding authority.
        5. Standardized declaration when context is insufficient.
        """
        system_instruction = (
            "You are FinCheck AI, a strict, authoritative regulatory and financial knowledge assistant "
            "for a retail bank's wealth management division.\n\n"
            "CRITICAL OPERATIONAL RULES:\n"
            "1. STRICT GROUNDING: Answer the user's question using ONLY the factual statements contained in the "
            "RETRIEVED CONTEXT below. Do NOT use outside knowledge, unverified assumptions, or extrapolation.\n"
            "2. REGULATORY PRIORITY: When both RBI Circulars ([Dataset: RBI Circular]) and Indian Financial Inclusion guides "
            "([Dataset: Indian Finance]) are provided, prioritize official Reserve Bank of India (RBI) circulars as the primary, "
            "binding regulatory authority.\n"
            "3. MANDATORY CITATIONS: Every factual statement, limit, deadline, or requirement in your answer MUST include "
            "an inline citation matching the source number, such as [Source 1], [Source 2]. Never make a claim without citing.\n"
            "4. INSUFFICIENT CONTEXT: If the retrieved documents do not contain sufficient factual details to answer the user's "
            "question completely and accurately, you MUST explicitly state:\n"
            "'The provided bank documents do not contain sufficient information to answer this question.'\n"
            "Explain specifically what information is present versus what is missing. Never invent interest rates, penalty percentages, "
            "tenures, or statutory exemptions.\n"
            "5. PROFESSIONAL TONE: Provide a clear, well-structured answer suitable for wealth advisors and bank compliance officers. "
            "Use bullet points and bold highlights where appropriate for readability."
        )

        context_blocks: List[str] = []
        for idx, chunk in enumerate(chunks, 1):
            dataset_label = (
                "RBI Circular"
                if chunk.source_dataset == "rbi"
                else "Indian Finance"
            )
            section_info = ""
            if chunk.metadata and chunk.metadata.get("section"):
                section_info = f" | Section: {chunk.metadata['section']}"

            clean_content = chunk.content.strip()
            block = (
                f"[Source {idx}] (Dataset: {dataset_label} | Document: {chunk.document_name}{section_info})\n"
                f"{clean_content}"
            )
            context_blocks.append(block)

        context_text = "\n\n---\n\n".join(context_blocks)
        user_prompt = (
            f"RETRIEVED CONTEXT FROM VERIFIED BANK DOCUMENTS:\n\n"
            f"{context_text}\n\n"
            f"==================================================\n"
            f"USER FINANCIAL QUESTION:\n"
            f"{question.strip()}\n\n"
            f"Provide a grounded, professional answer with inline [Source N] citations strictly based on the context above."
        )

        return system_instruction, user_prompt

    @staticmethod
    def extract_citations(answer_text: str) -> List[int]:
        """
        Extracts all unique [Source N] citation integers from the answer text in numerical order.
        """
        matches = re.findall(r"\[Source\s+(\d+)\]", answer_text, re.IGNORECASE)
        citation_ids: Set[int] = set()
        for m in matches:
            try:
                citation_ids.add(int(m))
            except ValueError:
                continue
        return sorted(list(citation_ids))

    @staticmethod
    def is_insufficient_context(answer_text: str) -> bool:
        """
        Detects whether the model indicated insufficient context to answer the question.
        """
        patterns = [
            r"not contain sufficient information",
            r"insufficient (information|context|details)",
            r"no(t enough| information) available in the provided",
            r"cannot be answered from the provided",
            r"provided documents do not (mention|specify|contain)",
        ]
        lower = answer_text.lower()
        return any(re.search(p, lower) for p in patterns)

    def generate_answer(
        self,
        question: str,
        chunks: List[RetrievedChunk],
        temperature: Optional[float] = None,
        total_candidates: int = 0,
        reranked: bool = False,
    ) -> GenerateResponse:
        """
        Generates a grounded answer for a financial question using Gemini.
        
        Args:
            question: Cleaned user query.
            chunks: Ordered list of top retrieved/reranked chunks.
            temperature: Optional sampling temperature override.
            total_candidates: Total vector candidates retrieved before reranking.
            reranked: Whether reranking was applied.
            
        Returns:
            GenerateResponse domain model.
        """
        clean_q = question.strip()
        if not clean_q:
            raise ValueError("Question cannot be empty.")

        # If no chunks were retrieved at all
        if not chunks:
            return GenerateResponse(
                question=clean_q,
                answer=(
                    "The provided bank documents do not contain sufficient information to answer this question. "
                    "No relevant passages were found in the knowledge corpus matching your query."
                ),
                is_grounded=False,
                is_insufficient_context=True,
                sources=[],
                cited_source_ids=[],
                model=self.model,
                total_candidates=0,
                reranked=reranked,
            )

        self._validate_config()

        system_instruction, user_prompt = self.build_prompt(clean_q, chunks)
        temp = temperature if temperature is not None else self.temperature

        # Build Gemini REST API request payload
        endpoint = f"{self.api_url.rstrip('/')}/{self.model}:generateContent?key={self.api_key}"
        payload = {
            "contents": [
                {
                    "role": "user",
                    "parts": [{"text": user_prompt}],
                }
            ],
            "systemInstruction": {
                "parts": [{"text": system_instruction}],
            },
            "generationConfig": {
                "temperature": temp,
                "maxOutputTokens": self.max_tokens,
            },
        }

        headers = {
            "Content-Type": "application/json",
        }

        last_error = None
        for attempt in range(1, self.max_retries + 1):
            try:
                with httpx.Client(timeout=self.timeout_seconds) as client:
                    response = client.post(endpoint, headers=headers, json=payload)

                # Rate limiting (429) or transient server error (5xx)
                if response.status_code == 429 or response.status_code >= 500:
                    wait_time = self.backoff_factor ** attempt
                    logger.warning(
                        f"Gemini API returned HTTP {response.status_code}. "
                        f"Retrying in {wait_time:.1f}s (attempt {attempt}/{self.max_retries})..."
                    )
                    time.sleep(wait_time)
                    continue

                response.raise_for_status()
                data = response.json()

                candidates = data.get("candidates", [])
                if not candidates:
                    raise GenerationError("Gemini API returned an empty candidates list.")

                content_parts = candidates[0].get("content", {}).get("parts", [])
                if not content_parts:
                    raise GenerationError("Gemini candidate response contained no text parts.")

                answer_text = content_parts[0].get("text", "").strip()
                if not answer_text:
                    raise GenerationError("Gemini generated blank answer text.")

                cited_ids = self.extract_citations(answer_text)
                insufficient = self.is_insufficient_context(answer_text)

                return GenerateResponse(
                    question=clean_q,
                    answer=answer_text,
                    is_grounded=not insufficient,
                    is_insufficient_context=insufficient,
                    sources=chunks,
                    cited_source_ids=cited_ids,
                    model=self.model,
                    total_candidates=total_candidates,
                    reranked=reranked,
                )

            except httpx.HTTPStatusError as e:
                # Mask out any URL query parameters (which may hold the api_key)
                last_error = f"HTTP {e.response.status_code}: {e.response.text[:200]}"
                wait_time = self.backoff_factor ** attempt
                logger.warning(
                    f"Gemini HTTP error (attempt {attempt}/{self.max_retries}): {last_error}. Retrying in {wait_time:.1f}s..."
                )
                time.sleep(wait_time)
            except Exception as e:
                last_error = str(e)
                wait_time = self.backoff_factor ** attempt
                logger.warning(
                    f"Gemini connection error (attempt {attempt}/{self.max_retries}): {last_error}. Retrying in {wait_time:.1f}s..."
                )
                time.sleep(wait_time)

        raise GenerationError(
            f"Failed to generate answer after {self.max_retries} attempts. Last error: {last_error}"
        )

    def create_fallback_response(
        self,
        question: str,
        chunks: List[RetrievedChunk],
        reason: str,
        total_candidates: int = 0,
        reranked: bool = False,
    ) -> GenerateResponse:
        """
        Creates a graceful fallback response when Gemini is temporarily unavailable or misconfigured.
        Presents the retrieved sources directly so the user still receives relevant knowledge.
        """
        fallback_msg = (
            "**Notice:** Automated answer generation is temporarily unavailable "
            f"({reason}). Below are the top verified source passages retrieved and reranked for your query."
        )
        return GenerateResponse(
            question=question,
            answer=fallback_msg,
            is_grounded=False,
            is_insufficient_context=False,
            sources=chunks,
            cited_source_ids=[],
            model=f"{self.model} (fallback)",
            total_candidates=total_candidates,
            reranked=reranked,
        )


# Global singleton service instance
generation_service = GenerationService()

"""
app/core/embeddings.py

Shared Embedding Service — encapsulated OpenAI embedding generation logic.
Reused by RAGService and DestinationService to follow DRY principles.
"""

import hashlib
import logging
import math
from openai import AsyncOpenAI
from app.core.config import get_settings
from app.core.exceptions import ValidationException

logger = logging.getLogger(__name__)

EMBEDDING_MODEL = "text-embedding-3-small"
EMBEDDING_DIMENSIONS = 1536


def generate_deterministic_embedding(text: str, dim: int = EMBEDDING_DIMENSIONS) -> list[float]:
    """
    Generate a deterministic 1536-dim normalized vector for local dev/testing
    when OPENAI_API_KEY is not configured.
    """
    words = text.lower().split()
    vec = [0.0] * dim
    for word in words:
        h = hashlib.sha256(word.encode("utf-8")).digest()
        for i in range(0, len(h), 2):
            idx = int.from_bytes(h[i:i+2], "big") % dim
            val = (h[i] / 255.0) - 0.5
            vec[idx] += val

    norm = math.sqrt(sum(x * x for x in vec))
    if norm > 0:
        return [x / norm for x in vec]
    vec[0] = 1.0
    return vec


class EmbeddingService:
    """Service class responsible for generating text vector embeddings via OpenAI with dev fallback."""

    def __init__(self, api_key: str | None = None) -> None:
        settings = get_settings()
        self.api_key = api_key or settings.OPENAI_API_KEY or ""
        self.client = AsyncOpenAI(api_key=self.api_key if self.api_key else "dummy-key-for-tests")

    async def generate_embeddings(self, texts: list[str]) -> list[list[float]]:
        """Generate vector embeddings for a list of text strings."""
        if not texts:
            return []

        # If valid OPENAI_API_KEY is present, call OpenAI API
        if self.api_key and self.api_key != "dummy-key-for-tests" and not self.api_key.startswith("CHANGE_THIS"):
            try:
                response = await self.client.embeddings.create(
                    model=EMBEDDING_MODEL,
                    input=texts
                )
                return [data.embedding for data in response.data]
            except Exception as e:
                logger.warning("OpenAI Embedding API call failed, falling back to local vector generator: %s", str(e))

        # Local deterministic vector generation fallback when OpenAI key is missing or offline
        return [generate_deterministic_embedding(text) for text in texts]

    async def generate_embedding(self, text: str) -> list[float]:
        """Generate a single vector embedding for a query string."""
        if not text or not text.strip():
            return []
        embeddings = await self.generate_embeddings([text.strip()])
        return embeddings[0] if embeddings else []

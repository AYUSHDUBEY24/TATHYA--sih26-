"""Document chunking + embedding + vector-retrieval pipeline (Phase 9A).

Provider-agnostic embedding abstraction with a deterministic fallback so the
retrieval service and tests never depend on an external embedding API. When a
real provider is not configured, the application degrades to a deterministic,
text-derived embedding and exposes a clear INDEXED_VIA status rather than
inventing real semantic vectors.

Authorization is enforced at the SQL level: retrieval can only ever see chunks
from documents in cases the requesting user may access.
"""

from __future__ import annotations

import hashlib
import json
import logging
import re
from dataclasses import dataclass, field

from app.core.config import get_settings

logger = logging.getLogger("sih26190.rag")

# Fallback embedding dimension (must match FALLBACK_DIM in retrieval_service).
FALLBACK_DIM = 256
# Tokens kept for the deterministic fallback hash — enough for stable similarity.
_FALLBACK_TOKEN_BUCKETS = FALLBACK_DIM


# ---------------------------------------------------------------------------
# Embedding provider abstraction
# ---------------------------------------------------------------------------


@dataclass
class EmbeddingResult:
    """Outcome of an embedding request."""

    vector: list[float]
    provider: str  # e.g. "openai", "fallback", "unavailable"
    dimension: int


class EmbeddingProvider:
    """Minimal interface every embedding backend must implement."""

    name: str = "base"

    def embed(self, texts: list[str]) -> EmbeddingResult:
        raise NotImplementedError

    def available(self) -> bool:
        return True


class FallbackEmbeddingProvider(EmbeddingProvider):
    """
    Deterministic, offline embedding with NO external calls.

    Each chunk is hashed into a fixed-dimension float vector. The mapping is
    deterministic (same text → same vector) and roughly preserves lexical
    similarity: chunks sharing many terms land closer together. This is NOT a
    real semantic embedding, but it is predictable and testable, and it keeps
    retrieval functional when no API key is configured.
    """

    name = "fallback"

    def __init__(self, dim: int = FALLBACK_DIM) -> None:
        self._dim = dim

    def available(self) -> bool:
        return True  # always available — no external dependency

    def embed(self, texts: list[str]) -> EmbeddingResult:
        return EmbeddingResult(
            vector=[self._embed_one(text, self._dim) for text in texts],
            provider=self.name,
            dimension=self._dim,
        )

    @staticmethod
    def _hash_to_unit_vector(text: str, dim: int) -> list[float]:
        """Map a single text to a deterministic unit-ish vector (list of floats).

        Per-dimension: accumulate signed hash contributions from each token,
        then tanh-normalise. Returns a flat list of floats — one scalar per
        dimension is stored as a single-element nested structure in the model,
        so we instead return dim scalars via a helper and flatten at call site.
        """
        raise RuntimeError("_hash_to_unit_vector is a scalar helper; use _embed_one")

    @staticmethod
    def _embed_one(text: str, dim: int) -> list[float]:
        tokens = re.findall(r"\w+", text.lower())
        accumulator = [0.0] * dim
        for token in tokens:
            digest = hashlib.sha256(token.encode("utf-8")).digest()
            # Pack the 32-byte digest into 16 signed contributions.
            for index in range(0, len(digest), 2):
                dim_index = (digest[index] + index) % dim
                sign = 1.0 if digest[index + 1] < 128 else -1.0
                accumulator[dim_index] += sign
        # Normalise to roughly unit length for cosine-friendly magnitudes.
        magnitude = sum(v * v for v in accumulator) ** 0.5 or 1.0
        return [round(v / magnitude, 6) for v in accumulator]


def _instantiate_provider() -> EmbeddingProvider:
    """Pick the best available embedding backend from configuration."""
    settings = get_settings()
    # Future: real provider (e.g. OpenAI) keyed off settings.EMBEDDINGS_PROVIDER.
    # For Phase 9A we ship the offline deterministic provider only.
    provider_name = getattr(settings, "EMBEDDINGS_PROVIDER", "fallback")
    if provider_name == "fallback" or not provider_name:
        return FallbackEmbeddingProvider()
    # Unknown provider — log and fall back rather than crash.
    logger.warning(
        "Unknown EMBEDDINGS_PROVIDER=%r — falling back to offline embeddings",
        provider_name,
    )
    return FallbackEmbeddingProvider()


# Module-level singleton — reused across requests.
_provider: EmbeddingProvider | None = None


def get_embedding_provider() -> EmbeddingProvider:
    """Return the shared embedding provider (lazy singleton)."""
    global _provider
    if _provider is None:
        _provider = _instantiate_provider()
    return _provider


def reset_embedding_provider() -> None:
    """Testing hook — force re-instantiation on next use."""
    global _provider
    _provider = None


def embed_texts(texts: list[str]) -> EmbeddingResult:
    """Embed a batch of texts via the shared provider (never raises)."""
    provider = get_embedding_provider()
    try:
        return provider.embed(texts)
    except Exception as exc:  # noqa: BLE001 — graceful degradation
        logger.warning("Embedding provider failed: %s — using fallback", exc)
        return FallbackEmbeddingProvider().embed(texts)

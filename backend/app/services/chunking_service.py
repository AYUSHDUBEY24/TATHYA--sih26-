"""
Deterministic document chunking (Phase 9A).

Converts extracted document text into fixed-size, overlapping chunks suitable
for embedding and RAG retrieval. The strategy is intentionally simple and
deterministic: the same input text always produces the same chunk list.

Strategy:
  1. Split text on paragraph breaks (double newlines).
  2. Greedily pack paragraphs into chunks up to ~target_size characters.
  3. Apply a sliding-window overlap so boundary context is preserved.
  4. Best-effort page assignment when page boundaries are known.

Chunks carry only positional metadata — no sensitive content beyond the chunk
text itself, which is always derived from already-authorized document text.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field

logger = logging.getLogger("sih26190.chunking")

# Target chunk size in characters (~500-1000 words for typical English text).
TARGET_CHUNK_CHARS = 800
# Overlap between consecutive chunks (preserves context at boundaries).
OVERLAP_CHARS = 100
# Minimum chunk size — smaller trailing text is merged into the previous chunk.
_MIN_CHUNK_CHARS = 100


@dataclass
class Chunk:
    """A single derived chunk, ready for embedding."""

    index: int
    text: str
    page_start: int | None = None
    page_end: int | None = None


@dataclass
class ChunkingResult:
    """Outcome of chunking a document text."""

    chunks: list[Chunk] = field(default_factory=list)
    total_chars: int = 0
    chunk_count: int = 0


def _split_paragraphs(text: str) -> list[str]:
    """Split on double newlines; fall back to single newlines if needed."""
    paragraphs = [p.strip() for p in text.split("\n\n") if p.strip()]
    if len(paragraphs) <= 1:
        paragraphs = [p.strip() for p in text.split("\n") if p.strip()]
    return paragraphs


def _split_oversized_chunks(
    chunks: list[Chunk], target_size: int, overlap: int
) -> list[Chunk]:
    """Re-split any chunk larger than ``target_size`` into word windows.

    A single paragraph without internal breaks (e.g. one enormous wall of text)
    would otherwise never be split by the paragraph-packing loop. The modest
    overlap is carried between consecutive windows. A single word longer than
    the target is kept whole — word granularity is the smallest unit.
    """
    result: list[Chunk] = []
    index = 0
    for chunk in chunks:
        if len(chunk.text) <= target_size:
            chunk.index = index
            result.append(chunk)
            index += 1
            continue

        window: list[str] = []
        window_len = 0
        for word in chunk.text.split():
            added = len(word) + (1 if window else 0)
            if window and window_len + added > target_size:
                piece = " ".join(window)
                result.append(
                    Chunk(
                        index=index,
                        text=piece,
                        page_start=chunk.page_start,
                        page_end=chunk.page_end,
                    )
                )
                index += 1
                # Carry the overlap tail (possibly mid-word) into the next window.
                if overlap and piece:
                    tail = piece[-overlap:]
                    window = [tail, word]
                    window_len = len(tail) + 1 + len(word)
                else:
                    window = [word]
                    window_len = len(word)
            else:
                window.append(word)
                window_len += added
        if window:
            result.append(
                Chunk(
                    index=index,
                    text=" ".join(window),
                    page_start=chunk.page_start,
                    page_end=chunk.page_end,
                )
            )
            index += 1
    return result


def chunk_text(
    text: str,
    *,
    page_count: int | None = None,
    target_size: int = TARGET_CHUNK_CHARS,
    overlap: int = OVERLAP_CHARS,
) -> ChunkingResult:
    """
    Deterministically chunk extracted text.

    Args:
        text: the full extracted document text.
        page_count: optional total page count for coarse page assignment.
        target_size: maximum characters per chunk.
        overlap: characters of overlap between consecutive chunks.
    """
    cleaned = text.strip()
    if not cleaned:
        return ChunkingResult()

    paragraphs = _split_paragraphs(cleaned)
    chunks: list[Chunk] = []
    current_parts: list[str] = []
    index = 0

    def _current_length() -> int:
        return sum(len(p) for p in current_parts) + max(0, len(current_parts) - 1)

    def _page_for_position(char_ratio: float) -> int | None:
        if not page_count:
            return None
        return min(page_count, max(1, int(char_ratio * page_count) + 1))

    def _flush(end_ratio: float) -> None:
        nonlocal index
        body = " ".join(current_parts).strip()
        if not body:
            return
        start_ratio = max(0.0, end_ratio - len(body) / max(1, len(cleaned)))
        chunks.append(
            Chunk(
                index=index,
                text=body,
                page_start=_page_for_position(start_ratio),
                page_end=_page_for_position(end_ratio),
            )
        )
        index += 1

    running_chars = 0
    for para in paragraphs:
        if current_parts and _current_length() + 1 + len(para) > target_size:
            _flush(running_chars / max(1, len(cleaned)))
            # Carry overlap context forward.
            if overlap and current_parts:
                tail = " ".join(current_parts)[-overlap:]
                current_parts = [tail, para]
            else:
                current_parts = [para]
        else:
            current_parts.append(para)
        running_chars += len(para) + 2  # +2 for the "\n\n" separator

    _flush(1.0)

    # A single very long paragraph (no internal breaks) can still exceed the
    # target size — split oversized chunks into bounded word windows so every
    # chunk is roughly target_size with the modest overlap preserved.
    if any(len(c.text) > target_size for c in chunks):
        chunks = _split_oversized_chunks(chunks, target_size, overlap)

    # Merge a too-small trailing chunk into its predecessor.
    if len(chunks) >= 2 and len(chunks[-1].text) < _MIN_CHUNK_CHARS:
        tail = chunks.pop()
        chunks[-1] = Chunk(
            index=chunks[-1].index,
            text=chunks[-1].text + " " + tail.text,
            page_start=chunks[-1].page_start,
            page_end=tail.page_end,
        )

    return ChunkingResult(
        chunks=chunks,
        total_chars=len(cleaned),
        chunk_count=len(chunks),
    )


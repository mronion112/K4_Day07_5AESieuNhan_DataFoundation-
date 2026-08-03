from __future__ import annotations

import math 
import re


class FixedSizeChunker:
    """
    Split text into fixed-size chunks with optional overlap.

    Rules:
        - Each chunk is at most chunk_size characters long.
        - Consecutive chunks share overlap characters.
        - The last chunk contains whatever remains.
        - If text is shorter than chunk_size, return [text].
    """

    def __init__(self, chunk_size: int = 500, overlap: int = 50) -> None:
        self.chunk_size = chunk_size
        self.overlap = overlap

    def chunk(self, text: str) -> list[str]:
        if not text:
            return []
        if len(text) <= self.chunk_size:
            return [text]

        step = self.chunk_size - self.overlap
        chunks: list[str] = []
        for start in range(0, len(text), step):
            chunk = text[start : start + self.chunk_size]
            chunks.append(chunk)
            if start + self.chunk_size >= len(text):
                break
        return chunks


class SentenceChunker:

    def __init__(self, max_sentences_per_chunk: int = 3) -> None:
        self.max_sentences_per_chunk = max(1, max_sentences_per_chunk)

    def chunk(self, text: str) -> list[str]:
        _SENTENCE_SPLIT_RE = re.compile(r"(?<=[.!?])(?:\s+|\n+)")

        text = text.strip()
        if not text:
            return []

        sentences = [
            sentence.strip()
            for sentence in self._SENTENCE_SPLIT_RE.split(text)
            if sentence.strip()
        ]

        chunks = []
        for i in range(0, len(sentences), self.max_sentences_per_chunk):
            chunk = " ".join(sentences[i : i + self.max_sentences_per_chunk])
            chunks.append(chunk)

        return chunks



class RecursiveChunker:
    """
    Recursively split text using separators in priority order.

    Default separator priority:
        ["\n\n", "\n", ". ", " ", ""]
    """

    DEFAULT_SEPARATORS = ["\n\n", "\n", ". ", " ", ""]

    def __init__(self, separators: list[str] | None = None, chunk_size: int = 500) -> None:
        self.separators = self.DEFAULT_SEPARATORS if separators is None else list(separators)
        self.chunk_size = chunk_size

    def chunk(self, text: str) -> list[str]:
        text = text.strip()
        if not text:
            return []

        return [c.strip() for c in self._split(text, self.separators) if c.strip()]

    def _split(
        self,
        current_text: str,
        remaining_separators: list[str],
    ) -> list[str]:
        current_text = current_text.strip()

        if len(current_text) <= self.chunk_size:
            return [current_text]

        # No separator left -> hard split
        if not remaining_separators:
            return [
                current_text[i : i + self.chunk_size]
                for i in range(0, len(current_text), self.chunk_size)
            ]

        separator = remaining_separators[0]
        next_separators = remaining_separators[1:]

        # Final fallback: character-level split
        if separator == "":
            return [
                current_text[i : i + self.chunk_size]
                for i in range(0, len(current_text), self.chunk_size)
            ]

        pieces = current_text.split(separator)

        chunks: list[str] = []
        buffer = ""

        for piece in pieces:
            piece = piece.strip()
            if not piece:
                continue

            candidate = (
                piece
                if not buffer
                else buffer + separator + piece
            )

            if len(candidate) <= self.chunk_size:
                buffer = candidate
            else:
                if buffer:
                    chunks.extend(self._split(buffer, next_separators))
                buffer = piece

        if buffer:
            chunks.extend(self._split(buffer, next_separators))

        return chunks

def _dot(a: list[float], b: list[float]) -> float:
    return sum(x * y for x, y in zip(a, b))


def compute_similarity(vec_a: list[float], vec_b: list[float]) -> float:
    """
    Compute cosine similarity between two vectors.

    cosine_similarity = dot(a, b) / (||a|| * ||b||)

    Returns 0.0 if either vector has zero magnitude.
    """
    if len(vec_a) != len(vec_b):
        raise ValueError("Vectors must have the same length.")

    dot = sum(a * b for a, b in zip(vec_a, vec_b))
    norm_a = math.sqrt(sum(a * a for a in vec_a))
    norm_b = math.sqrt(sum(b * b for b in vec_b))

    if norm_a == 0 or norm_b == 0:
        return 0.0

    return dot / (norm_a * norm_b)

class ChunkingStrategyComparator:
    """Run all built-in chunking strategies and compare their results."""

    def compare(self, text: str, chunk_size: int = 200) -> dict:
        strategies = {
            "fixed": FixedSizeChunker(chunk_size),
            "sentence": SentenceChunker(),
            "recursive": RecursiveChunker(chunk_size=chunk_size),
        }

        results = {}

        for name, chunker in strategies.items():
            chunks = chunker.chunk(text)

            lengths = [len(c) for c in chunks]

            results[name] = {
                "num_chunks": len(chunks),
                "avg_chunk_length": (
                    sum(lengths) / len(lengths) if lengths else 0
                ),
                "max_chunk_length": max(lengths, default=0),
                "min_chunk_length": min(lengths, default=0),
                "chunks": chunks,
            }

        return results
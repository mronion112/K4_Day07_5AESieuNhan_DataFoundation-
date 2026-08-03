from __future__ import annotations

import math
import re


class FixedSizeChunker:
    def __init__(self, chunk_size: int = 500, overlap: int = 50) -> None:
        self.chunk_size = chunk_size
        self.overlap = overlap

    def chunk(self, text: str) -> list[str]:
        if not text:
            return []

        if len(text) <= self.chunk_size:
            return [text]

        step = self.chunk_size - self.overlap
        chunks = []

        for start in range(0, len(text), step):
            chunk = text[start:start + self.chunk_size]
            chunks.append(chunk)

            if start + self.chunk_size >= len(text):
                break

        return chunks


class SentenceChunker:
    def __init__(self, max_sentences_per_chunk: int = 3) -> None:
        self.max_sentences_per_chunk = max(1, max_sentences_per_chunk)

    def chunk(self, text: str) -> list[str]:
        if not text.strip():
            return []

        # split after ., !, ?
        sentences = re.split(r'(?<=[.!?])\s+', text.strip())
        sentences = [s.strip() for s in sentences if s.strip()]

        chunks = []

        for i in range(0, len(sentences), self.max_sentences_per_chunk):
            chunk = " ".join(sentences[i:i+self.max_sentences_per_chunk])
            chunks.append(chunk)

        return chunks


class RecursiveChunker:

    DEFAULT_SEPARATORS = ["\n\n", "\n", ". ", " ", ""]

    def __init__(self,
                 separators: list[str] | None = None,
                 chunk_size: int = 500) -> None:

        self.separators = separators or self.DEFAULT_SEPARATORS
        self.chunk_size = chunk_size

    def chunk(self, text: str) -> list[str]:
        if not text.strip():
            return []

        return self._split(text, self.separators)

    def _split(
        self,
        current_text: str,
        remaining_separators: list[str]
    ) -> list[str]:

        if len(current_text) <= self.chunk_size:
            return [current_text.strip()]

        if not remaining_separators:
            return [
                current_text[i:i+self.chunk_size]
                for i in range(0, len(current_text), self.chunk_size)
            ]

        separator = remaining_separators[0]

        # last fallback
        if separator == "":
            return [
                current_text[i:i+self.chunk_size]
                for i in range(0, len(current_text), self.chunk_size)
            ]

        pieces = current_text.split(separator)

        chunks = []
        current = ""

        for piece in pieces:

            candidate = piece if not current else current + separator + piece

            if len(candidate) <= self.chunk_size:
                current = candidate
            else:

                if current:
                    chunks.extend(
                        self._split(current, remaining_separators[1:])
                    )

                current = piece

        if current:
            chunks.extend(
                self._split(current, remaining_separators[1:])
            )

        return chunks


def _dot(a: list[float], b: list[float]) -> float:
    return sum(x * y for x, y in zip(a, b))


def compute_similarity(vec_a: list[float], vec_b: list[float]) -> float:

    if len(vec_a) != len(vec_b):
        raise ValueError("Vectors must have same length")

    norm_a = math.sqrt(sum(x * x for x in vec_a))
    norm_b = math.sqrt(sum(x * x for x in vec_b))

    if norm_a == 0 or norm_b == 0:
        return 0.0

    return _dot(vec_a, vec_b) / (norm_a * norm_b)


class ChunkingStrategyComparator:

    def compare(
        self,
        text: str,
        chunk_size: int = 200
    ) -> dict:

        strategies = {
            "fixed_size": FixedSizeChunker(
                chunk_size=chunk_size,
                overlap=50
            ),
            "by_sentences": SentenceChunker(),
            "recursive": RecursiveChunker(
                chunk_size=chunk_size
            ),
        }

        result = {}

        for name, strategy in strategies.items():

            chunks = strategy.chunk(text)
            count = len(chunks)
            avg_len = (sum(len(c) for c in chunks) / count) if count > 0 else 0.0

            result[name] = {
                "count": count,
                "num_chunks": count,
                "avg_length": avg_len,
                "avg_chunk_length": avg_len,
                "max_chunk_length": max((len(c) for c in chunks), default=0),
                "min_chunk_length": min((len(c) for c in chunks), default=0),
                "chunks": chunks,
            }

        return result


class MarkdownHeaderChunker:
    """
    Splits text by markdown headers (#, ##, ###, ####), maintaining section context.
    Ideal for structured policy documents like e-commerce terms & FAQs.
    """

    def __init__(self, max_chunk_size: int = 1000) -> None:
        self.max_chunk_size = max_chunk_size

    def chunk(self, text: str) -> list[str]:
        if not text.strip():
            return []

        # Split by header lines (lines starting with #)
        sections = re.split(r'(?m)^(#{1,6}\s+.*$)', text)

        chunks = []
        current_chunk = ""

        for section in sections:
            if not section.strip():
                continue
            if len(current_chunk) + len(section) <= self.max_chunk_size:
                current_chunk += section
            else:
                if current_chunk.strip():
                    chunks.append(current_chunk.strip())
                current_chunk = section

        if current_chunk.strip():
            chunks.append(current_chunk.strip())

        return chunks
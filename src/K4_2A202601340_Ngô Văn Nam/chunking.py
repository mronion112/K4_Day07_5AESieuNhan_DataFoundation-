from __future__ import annotations

import math
import re


class FixedSizeChunker:
    """Chia text theo kích thước cố định với overlap tùy chọn."""

    def __init__(self, chunk_size: int = 500, overlap: int = 50) -> None:
        if chunk_size <= 0:
            raise ValueError("chunk_size must be greater than zero")
        if overlap < 0 or overlap >= chunk_size:
            raise ValueError("overlap must satisfy 0 <= overlap < chunk_size")
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
            chunks.append(text[start : start + self.chunk_size])
            if start + self.chunk_size >= len(text):
                break
        return chunks


class SentenceChunker:
    """Gom tối đa một số câu mà không bỏ dấu kết câu."""

    SENTENCE_BOUNDARY = re.compile(r"(?<=[.!?])(?:[ \t]+|\r?\n+)")

    def __init__(self, max_sentences_per_chunk: int = 3) -> None:
        self.max_sentences_per_chunk = max(1, max_sentences_per_chunk)

    def chunk(self, text: str) -> list[str]:
        if not text or not text.strip():
            return []
        sentences = [
            sentence.strip()
            for sentence in self.SENTENCE_BOUNDARY.split(text.strip())
            if sentence.strip()
        ]
        limit = self.max_sentences_per_chunk
        return [
            " ".join(sentences[index : index + limit])
            for index in range(0, len(sentences), limit)
        ]


class RecursiveChunker:
    """Chia đệ quy theo đoạn, dòng, câu, từ rồi ký tự."""

    DEFAULT_SEPARATORS = ["\n\n", "\n", ". ", " ", ""]

    def __init__(self, separators: list[str] | None = None, chunk_size: int = 500) -> None:
        if chunk_size <= 0:
            raise ValueError("chunk_size must be greater than zero")
        self.separators = self.DEFAULT_SEPARATORS if separators is None else list(separators)
        self.chunk_size = chunk_size

    def chunk(self, text: str) -> list[str]:
        if not text or not text.strip():
            return []
        return [piece for piece in self._split(text.strip(), self.separators) if piece]

    def _split(self, current_text: str, remaining_separators: list[str]) -> list[str]:
        if len(current_text) <= self.chunk_size:
            return [current_text]
        if not remaining_separators or remaining_separators[0] == "":
            return [
                current_text[index : index + self.chunk_size]
                for index in range(0, len(current_text), self.chunk_size)
            ]
        separator = remaining_separators[0]
        lower_priority = remaining_separators[1:]
        if separator not in current_text:
            return self._split(current_text, lower_priority)

        chunks: list[str] = []
        buffer = ""
        for raw_part in current_text.split(separator):
            part = raw_part.strip()
            if not part:
                continue
            candidate = part if not buffer else f"{buffer}{separator}{part}"
            if len(candidate) <= self.chunk_size:
                buffer = candidate
                continue
            if buffer:
                chunks.append(buffer)
            if len(part) > self.chunk_size:
                chunks.extend(self._split(part, lower_priority))
                buffer = ""
            else:
                buffer = part
        if buffer:
            chunks.append(buffer)
        return chunks


def _dot(a: list[float], b: list[float]) -> float:
    return sum(x * y for x, y in zip(a, b))


def compute_similarity(vec_a: list[float], vec_b: list[float]) -> float:
    norm_a = math.sqrt(_dot(vec_a, vec_a))
    norm_b = math.sqrt(_dot(vec_b, vec_b))
    if norm_a == 0.0 or norm_b == 0.0:
        return 0.0
    return _dot(vec_a, vec_b) / (norm_a * norm_b)


class ChunkingStrategyComparator:
    """Chạy ba chunker nền tảng và tóm tắt kết quả."""

    def compare(self, text: str, chunk_size: int = 200) -> dict:
        strategies = {
            "fixed_size": FixedSizeChunker(chunk_size, max(0, chunk_size // 10)),
            "by_sentences": SentenceChunker(3),
            "recursive": RecursiveChunker(chunk_size=chunk_size),
        }
        comparison: dict = {}
        for name, strategy in strategies.items():
            chunks = strategy.chunk(text)
            comparison[name] = {
                "count": len(chunks),
                "avg_length": sum(map(len, chunks)) / len(chunks) if chunks else 0.0,
                "chunks": chunks,
            }
        return comparison

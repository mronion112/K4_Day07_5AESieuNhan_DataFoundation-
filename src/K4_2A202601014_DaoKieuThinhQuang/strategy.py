from __future__ import annotations

import re

from .chunking import RecursiveChunker


class HeadingRecursiveChunker:
    """Split policy documents by headings, then recursively split long sections.

    Each fragment created from a long section receives the section heading again,
    so retrieved fragments keep their local policy context.
    """

    MARKDOWN_HEADING = re.compile(r"^#{1,6}\s+\S")
    NUMBERED_HEADING = re.compile(r"^(?:[A-Z]\.|\d+(?:\.\d+)*\.?)\s+\S")

    def __init__(self, chunk_size: int = 2000, overlap: int = 300) -> None:
        if chunk_size <= 0:
            raise ValueError("chunk_size must be greater than zero")
        if overlap < 0 or overlap >= chunk_size:
            raise ValueError("overlap must satisfy 0 <= overlap < chunk_size")
        self.chunk_size = chunk_size
        self.overlap = overlap

    @classmethod
    def _is_heading(cls, line: str) -> bool:
        stripped = line.strip()
        if not stripped:
            return False
        if cls.MARKDOWN_HEADING.match(stripped):
            return True
        # Corpus headings are short numbered/lettered lines. The length guard
        # prevents long numbered policy clauses from becoming headings.
        return len(stripped) <= 160 and bool(cls.NUMBERED_HEADING.match(stripped))

    def chunk(self, text: str) -> list[str]:
        if not text or not text.strip():
            return []

        sections: list[tuple[str, list[str]]] = []
        current_heading = ""
        current_body: list[str] = []

        for line in text.splitlines():
            if self._is_heading(line):
                if current_heading or any(part.strip() for part in current_body):
                    sections.append((current_heading, current_body))
                current_heading = line.strip()
                current_body = []
            else:
                current_body.append(line)

        if current_heading or any(part.strip() for part in current_body):
            sections.append((current_heading, current_body))

        chunks: list[str] = []
        pending_headings: list[str] = []
        for heading, body_lines in sections:
            body = "\n".join(body_lines).strip()
            if not body:
                # A standalone parent heading is useful context, but not a useful
                # retrieval record. Carry it into the next section instead.
                if heading:
                    pending_headings.append(heading)
                continue

            effective_heading = "\n".join(
                part for part in (*pending_headings, heading) if part
            )
            pending_headings = []
            chunks.extend(self._chunk_section(effective_heading, body))
        return [chunk for chunk in chunks if chunk]

    def _chunk_section(self, heading: str, body: str) -> list[str]:
        full_section = "\n\n".join(part for part in (heading, body) if part).strip()
        if not full_section:
            return []
        if len(full_section) <= self.chunk_size:
            return [full_section]

        if not heading:
            return RecursiveChunker(chunk_size=self.chunk_size).chunk(body)

        body_limit = self.chunk_size - len(heading) - 2
        if body_limit <= 20:
            return RecursiveChunker(chunk_size=self.chunk_size).chunk(full_section)

        content_limit = body_limit - self.overlap - 1
        if content_limit <= 20:
            return RecursiveChunker(chunk_size=self.chunk_size).chunk(full_section)

        raw_chunks = RecursiveChunker(chunk_size=content_limit).chunk(body)
        body_chunks: list[str] = []
        for index, piece in enumerate(raw_chunks):
            if index == 0 or self.overlap == 0:
                body_chunks.append(piece)
                continue

            tail = raw_chunks[index - 1][-self.overlap :]
            if " " in tail:
                tail = tail.split(" ", 1)[1]
            body_chunks.append(f"{tail.strip()}\n{piece}")

        return [f"{heading}\n\n{piece}" for piece in body_chunks]

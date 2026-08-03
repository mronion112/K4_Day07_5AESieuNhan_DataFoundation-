"""Chunker theo heading/section dành cho tài liệu chính sách."""

from __future__ import annotations

import re

from .chunking import RecursiveChunker


class HeadingSectionChunker:
    """Tách trước heading/điều khoản, rồi recursive nếu section còn quá dài.

    Tiêu đề được gắn lại vào từng mảnh con để các mảnh sau không mất ngữ cảnh.
    """

    HEADING_PATTERN = re.compile(
        r"^(?:#{1,6}\s+|[A-ZĐ]\.[ \t]+\S|\d+(?:\.\d+)*\.?[ \t]+\S)"
    )
    MAX_HEADING_LENGTH = 180

    def __init__(self, chunk_size: int = 800) -> None:
        self.chunk_size = chunk_size

    def chunk(self, text: str) -> list[str]:
        if not text or not text.strip():
            return []

        sections: list[tuple[str | None, list[str]]] = []
        heading: str | None = None
        body: list[str] = []

        for raw_line in text.strip().splitlines():
            line = raw_line.strip()
            if not line:
                if body and body[-1] != "":
                    body.append("")
                continue
            if (
                len(line) <= self.MAX_HEADING_LENGTH
                and self.HEADING_PATTERN.match(line)
            ):
                if heading is not None or any(part.strip() for part in body):
                    sections.append((heading, body))
                heading = line
                body = []
            else:
                body.append(line)

        if heading is not None or any(part.strip() for part in body):
            sections.append((heading, body))

        chunks: list[str] = []
        for section_heading, section_body in sections:
            body_text = "\n".join(section_body).strip()
            chunks.extend(self._split_section(section_heading, body_text))
        return [piece for piece in chunks if piece.strip()]

    def _split_section(self, heading: str | None, body: str) -> list[str]:
        prefix = f"{heading}\n" if heading else ""
        section = f"{prefix}{body}".strip()
        if not section:
            return []
        if len(section) <= self.chunk_size:
            return [section]

        if heading and not body:
            return RecursiveChunker(chunk_size=self.chunk_size).chunk(heading)

        available = max(1, self.chunk_size - len(prefix))
        pieces = RecursiveChunker(chunk_size=available).chunk(body or heading or "")
        if heading and body:
            return [f"{heading}\n{piece}".strip() for piece in pieces]
        return pieces

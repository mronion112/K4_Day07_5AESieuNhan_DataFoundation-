"""Bài làm cá nhân của DaoKieuThinhQuang — MSSV 2A202601014."""

from ..embeddings import MockEmbedder, _mock_embed
from ..models import Document
from .agent import KnowledgeBaseAgent
from .chunking import (
    ChunkingStrategyComparator,
    FixedSizeChunker,
    RecursiveChunker,
    SentenceChunker,
    compute_similarity,
)
from .store import EmbeddingStore
from .strategy import HeadingRecursiveChunker
from .personal_embeddings import VietnameseLexicalEmbedder

__all__ = [
    "Document",
    "FixedSizeChunker",
    "SentenceChunker",
    "RecursiveChunker",
    "ChunkingStrategyComparator",
    "compute_similarity",
    "EmbeddingStore",
    "KnowledgeBaseAgent",
    "MockEmbedder",
    "_mock_embed",
    "HeadingRecursiveChunker",
    "VietnameseLexicalEmbedder",
]

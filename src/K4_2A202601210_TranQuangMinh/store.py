from __future__ import annotations

from typing import Any, Callable

from .chunking import _dot
from .embeddings import _mock_embed
from .models import Document


class EmbeddingStore:
    """
    A vector store for text chunks.

    Tries to use ChromaDB if available; falls back to an in-memory store.
    The embedding_fn parameter allows injection of mock embeddings for tests.
    """

    def __init__(
        self,
        collection_name: str = "documents",
        embedding_fn: Callable[[str], list[float]] | None = None,
    ) -> None:
        self._embedding_fn = embedding_fn or _mock_embed
        self._collection_name = collection_name
        self._use_chroma = False
        self._store: list[dict[str, Any]] = []
        self._collection = None
        self._next_index = 0

        try:
            import chromadb  # noqa: F401

            # TODO: initialize chromadb client + collection
            self._use_chroma = True
        except Exception:
            self._use_chroma = False
            self._collection = None

    def _make_record(self, doc: Document) -> dict[str, Any]:
        # Tạo id duy nhất cho record này: doc.id + index tăng dần
        record_id = f"{doc.id}::{self._next_index}"
        self._next_index += 1

        # Copy metadata để không làm ảnh hưởng object gốc bên ngoài
        # Đảm bảo metadata luôn có doc_id để delete_document hoạt động
        metadata = dict(doc.metadata)
        metadata.setdefault("doc_id", doc.id)

        # Embed nội dung của document
        embedding = self._embedding_fn(doc.content)

        return {
            "id": record_id,
            "content": doc.content,
            "metadata": metadata,
            "embedding": embedding,
        }

    def _search_records(self, query: str, records: list[dict[str, Any]], top_k: int) -> list[dict[str, Any]]:
        # Embed query MỘT LẦN duy nhất, không gọi lại trong vòng lặp
        query_vector = self._embedding_fn(query)

        # Tính dot product giữa query vector và từng record embedding
        scored = []
        for record in records:
            score = _dot(query_vector, record["embedding"])
            scored.append({
                "id": record["id"],
                "content": record["content"],
                "metadata": record["metadata"],
                "score": score,
            })

        # Sort giảm dần theo score (điểm cao nhất = giống nhất lên đầu)
        scored.sort(key=lambda r: r["score"], reverse=True)

        # Trả về top_k kết quả
        return scored[:top_k]

    def add_documents(self, docs: list[Document]) -> None:
        # Duyệt từng Document, tạo record rồi append vào _store
        for doc in docs:
            record = self._make_record(doc)
            self._store.append(record)

    def search(self, query: str, top_k: int = 5) -> list[dict[str, Any]]:
        # Tìm trong toàn bộ store, không lọc
        return self._search_records(query, self._store, top_k)

    def get_collection_size(self) -> int:
        # Trả tổng số record hiện có trong store
        return len(self._store)

    def search_with_filter(self, query: str, top_k: int = 3, metadata_filter: dict = None) -> list[dict]:
        # Không có filter → hành vi giống search() thông thường
        if metadata_filter is None:
            return self.search(query, top_k=top_k)

        # Lọc: chỉ giữ record có metadata khớp TẤT CẢ cặp key/value trong filter
        # Lọc TRƯỚC, rồi mới search → đảm bảo không bị mất kết quả hợp lệ
        filtered = []
        for record in self._store:
            match = all(
                record["metadata"].get(key) == value
                for key, value in metadata_filter.items()
            )
            if match:
                filtered.append(record)

        # Search trên tập đã lọc
        return self._search_records(query, filtered, top_k)

    def delete_document(self, doc_id: str) -> bool:
        # Tìm tất cả record có metadata["doc_id"] == doc_id
        before = len(self._store)
        self._store = [
            r for r in self._store
            if r["metadata"].get("doc_id") != doc_id
        ]
        after = len(self._store)
        # Trả True nếu có ít nhất 1 record bị xoá
        return after < before

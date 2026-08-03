from __future__ import annotations

from typing import Callable

from .store import EmbeddingStore


class KnowledgeBaseAgent:
    """Trả lời từ context truy xuất và giữ provenance."""

    def __init__(self, store: EmbeddingStore, llm_fn: Callable[[str], str]) -> None:
        self.store = store
        self.llm_fn = llm_fn

    def answer(self, question: str, top_k: int = 3, metadata_filter: dict | None = None) -> str:
        results = (
            self.store.search(question, top_k)
            if metadata_filter is None
            else self.store.search_with_filter(question, top_k, metadata_filter)
        )
        if not results:
            return "Không tìm thấy ngữ cảnh phù hợp trong cơ sở tri thức để trả lời câu hỏi."

        context_parts: list[str] = []
        for index, result in enumerate(results, start=1):
            metadata = result.get("metadata", {})
            source = metadata.get("source_url") or metadata.get("source") or "không rõ nguồn"
            doc_id = metadata.get("doc_id") or result.get("id", "không rõ tài liệu")
            context_parts.append(f"[{index}] doc_id={doc_id}; source={source}\n{result['content']}")

        context = "\n\n".join(context_parts)
        prompt = (
            "Bạn là trợ lý hỏi đáp có dẫn nguồn. Chỉ sử dụng thông tin trong Context. "
            "Trích dẫn bằng [1], [2], ... và nói rõ nếu Context không đủ.\n\n"
            f"Context:\n{context}\n\nQuestion: {question}\nAnswer:"
        )
        return self.llm_fn(prompt)

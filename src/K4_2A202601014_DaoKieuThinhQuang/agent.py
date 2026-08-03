from __future__ import annotations

from typing import Callable

from .store import EmbeddingStore


class KnowledgeBaseAgent:
    """Answer questions using context retrieved from an embedding store."""

    def __init__(self, store: EmbeddingStore, llm_fn: Callable[[str], str]) -> None:
        self.store = store
        self.llm_fn = llm_fn

    def answer(
        self,
        question: str,
        top_k: int = 3,
        metadata_filter: dict | None = None,
    ) -> str:
        if metadata_filter is None:
            results = self.store.search(question, top_k=top_k)
        else:
            results = self.store.search_with_filter(
                question,
                top_k=top_k,
                metadata_filter=metadata_filter,
            )
        if not results:
            return "Không tìm thấy ngữ cảnh phù hợp trong cơ sở tri thức để trả lời câu hỏi."

        context_parts: list[str] = []
        for index, result in enumerate(results, start=1):
            metadata = result.get("metadata", {})
            source = metadata.get("source_url") or metadata.get("source") or "không rõ nguồn"
            doc_id = metadata.get("doc_id") or result.get("id", "không rõ tài liệu")
            context_parts.append(
                f"[{index}] doc_id={doc_id}; source={source}\n{result['content']}"
            )

        context = "\n\n".join(context_parts)
        prompt = (
            "Bạn là trợ lý hỏi đáp có dẫn nguồn. Chỉ sử dụng thông tin trong "
            "Context để trả lời. Trích dẫn nguồn bằng số [1], [2], ... tương ứng. "
            "Nếu Context không đủ thông tin, hãy nói rõ rằng chưa đủ thông tin.\n\n"
            f"Context:\n{context}\n\n"
            f"Question: {question}\n"
            "Answer:"
        )
        return self.llm_fn(prompt)

from typing import Callable

from .store import EmbeddingStore


class KnowledgeBaseAgent:
    """
    An agent that answers questions using a vector knowledge base.

    Retrieval-augmented generation (RAG) pattern:
        1. Retrieve top-k relevant chunks from the store.
        2. Build a prompt with the chunks as context.
        3. Call the LLM to generate an answer.
    """

    def __init__(self, store: EmbeddingStore, llm_fn: Callable[[str], str]) -> None:
        # Lưu reference đến store và hàm LLM
        self.store = store
        self.llm_fn = llm_fn

    def answer(self, question: str, top_k: int = 3) -> str:
        # Store rỗng → thông báo, không gọi LLM
        if self.store.get_collection_size() == 0:
            return "Knowledge base is empty. Please add documents first."

        # 1. Truy xuất top-k chunk liên quan nhất từ store
        results = self.store.search(question, top_k=top_k)

        # 2. Ghép context: đánh số [1], [2]... kèm doc_id để truy vết nguồn
        context_parts = []
        for i, r in enumerate(results, start=1):
            source = r["metadata"].get("doc_id", "unknown")
            context_parts.append(f"[{i}] (source: {source})\n{r['content']}")
        context = "\n\n".join(context_parts)

        # 3. Tạo prompt: hướng dẫn + context + câu hỏi
        prompt = (
            "You are a helpful assistant. Answer the question using ONLY the provided context below.\n"
            "If the context does not contain enough information, say so clearly.\n\n"
            f"Context:\n{context}\n\n"
            f"Question: {question}\n\n"
            "Answer:"
        )

        # 4. Gọi LLM (hàm giả lập hoặc thật) và trả kết quả
        return self.llm_fn(prompt)

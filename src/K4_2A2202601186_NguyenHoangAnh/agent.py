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
        self.store = store
        self.llm_fn = llm_fn

    def answer(self, question: str, top_k: int = 3) -> str:
        results = self.store.search(
            question,
            top_k=top_k,
        )

        if not results:
            return "Không tìm thấy thông tin phù hợp trong knowledge base."

        # 2. Build context
        contexts = []

        for i, item in enumerate(results, start=1):
            content = item.get("content", "")

            contexts.append(
                f"[Context {i}]\n{content}"
            )

        context_text = "\n\n".join(contexts)

        # 3. Build RAG prompt
        prompt = f"""
Bạn là trợ lý AI trả lời dựa trên context được cung cấp.

Chỉ sử dụng thông tin trong context để trả lời.
Nếu context không đủ thông tin, hãy nói rằng không có đủ dữ liệu.

Context:
{context_text}

Câu hỏi:
{question}

Trả lời:
""".strip()

        # 4. Generate answer
        return self.llm_fn(prompt)
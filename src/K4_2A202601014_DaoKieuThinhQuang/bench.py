from __future__ import annotations

import os
import re
import unicodedata
from pathlib import Path

import ingest as shared_ingest

from ..embeddings import LocalEmbedder, _mock_embed
from .agent import KnowledgeBaseAgent
from .benchmark_queries import BENCHMARK_CASES
from .chunking import ChunkingStrategyComparator
from .store import EmbeddingStore
from .strategy import HeadingRecursiveChunker
from .personal_embeddings import VietnameseLexicalEmbedder


DATA_DIR = Path("data/k4_ecommerce")
PREVIEW_LENGTH = 180
BASELINE_DOC_IDS = [
    "tra-hang-phuong-thuc-gui-hoan-tra",
    "chinh-sach-cam-han-che-san-pham",
    "chinh-sach-bao-mat",
]


def select_embedding_fn():
    """Use local neural embeddings when available, else a lexical baseline."""
    provider = os.getenv("EMBEDDING_PROVIDER", "lexical").strip().lower()
    if provider == "local":
        try:
            return LocalEmbedder()
        except Exception as exc:
            print(f"Không tải được local embedder ({exc}); chuyển sang mock.")
            return VietnameseLexicalEmbedder()
    if provider == "mock":
        return _mock_embed
    return VietnameseLexicalEmbedder()


def grounded_preview_llm(prompt: str) -> str:
    """Offline extractive fallback: return retrieved evidence with citations."""
    match = re.search(
        r"Context:\n(.*?)\n\nQuestion:",
        prompt,
        re.DOTALL,
    )
    if not match:
        return "Context chưa đủ để tạo câu trả lời."
    return f"[Offline extractive answer]\n{match.group(1).strip()}"


def normalize_text(text: str) -> str:
    decomposed = unicodedata.normalize("NFD", text.casefold())
    return "".join(char for char in decomposed if unicodedata.category(char) != "Mn")


def matched_evidence(case, text: str) -> list[bool]:
    normalized = normalize_text(text)
    return [
        any(normalize_text(marker) in normalized for marker in alternatives)
        for alternatives in case.evidence_groups
    ]


def evaluate_results(case, results: list[dict], answer: str | None = None) -> dict:
    combined_context = "\n".join(result["content"] for result in results)
    context_matches = matched_evidence(case, combined_context)
    per_chunk = [matched_evidence(case, result["content"]) for result in results]
    relevant_flags = [any(matches) for matches in per_chunk]
    coverage = sum(context_matches) / len(context_matches) if context_matches else 0.0
    first_relevant_rank = next(
        (index for index, relevant in enumerate(relevant_flags, start=1) if relevant),
        None,
    )
    answer_complete = bool(answer) and all(matched_evidence(case, answer))
    rubric_score = 2 if coverage == 1.0 and answer_complete else (1 if coverage > 0 else 0)
    return {
        "coverage": coverage,
        "matched_groups": sum(context_matches),
        "total_groups": len(context_matches),
        "per_chunk_relevant": relevant_flags,
        "first_relevant_rank": first_relevant_rank,
        "answer_complete": answer_complete,
        "rubric_score": rubric_score,
    }


def print_baseline() -> None:
    """Compare built-in strategies on bodies parsed without YAML front matter."""
    documents = {doc.id: doc for doc in shared_ingest.load_documents(DATA_DIR)}
    comparator = ChunkingStrategyComparator()
    print("=== BASELINE (chunk_size=400, front matter đã bỏ) ===")
    for doc_id in BASELINE_DOC_IDS:
        print(f"Document: {doc_id}")
        comparison = comparator.compare(documents[doc_id].content, chunk_size=400)
        for name, stats in comparison.items():
            print(
                f"  {name}: count={stats['count']} "
                f"avg_length={stats['avg_length']:.2f}"
            )


def build_store(chunker: HeadingRecursiveChunker, embedding_fn) -> EmbeddingStore:
    # Reuse the complete shared ingest pipeline while selecting the personal
    # in-memory store implementation for this benchmark process only.
    shared_ingest.EmbeddingStore = EmbeddingStore
    return shared_ingest.build_knowledge_base(
        DATA_DIR,
        embedding_fn=embedding_fn,
        chunker=chunker,
        collection_name="dao_kieu_thinh_quang_benchmark",
    )


def run_benchmark() -> None:
    print_baseline()
    chunker = HeadingRecursiveChunker(chunk_size=2000, overlap=300)  # strategy-specific line
    embedding_fn = select_embedding_fn()
    store = build_store(chunker, embedding_fn)
    agent = KnowledgeBaseAgent(store=store, llm_fn=grounded_preview_llm)

    backend = getattr(embedding_fn, "_backend_name", embedding_fn.__class__.__name__)
    print("=== BENCHMARK CÁ NHÂN ===")
    print("Strategy: HeadingRecursiveChunker")
    print(f"Parameters: chunk_size={chunker.chunk_size}, overlap={chunker.overlap}")
    print(f"Embedding backend: {backend}")
    print(f"Số chunk đã nạp: {store.get_collection_size()}")

    expected_doc_hits = 0
    evidence_hits = 0
    total_rubric_score = 0
    for index, case in enumerate(BENCHMARK_CASES, start=1):
        if case.metadata_filter:
            results = store.search_with_filter(
                case.query,
                top_k=3,
                metadata_filter=case.metadata_filter,
            )
        else:
            results = store.search(case.query, top_k=3)

        print(f"\n--- Query {index} ---")
        print(f"Question: {case.query}")
        print(f"Filter: {case.metadata_filter}")
        print(f"Expected: {case.expected_doc_id} ({case.expected_section})")
        print(f"Gold: {case.gold_answer}")
        print("Top-3:")
        retrieved_doc_ids = [result["metadata"].get("doc_id") for result in results]
        expected_rank = (
            retrieved_doc_ids.index(case.expected_doc_id) + 1
            if case.expected_doc_id in retrieved_doc_ids
            else None
        )
        if expected_rank is not None:
            expected_doc_hits += 1
        preliminary = evaluate_results(case, results)
        for rank, result in enumerate(results, start=1):
            metadata = result["metadata"]
            preview = " ".join(result["content"].split())[:PREVIEW_LENGTH]
            print(
                f"  {rank}. score={result['score']:.4f} "
                f"doc_id={metadata.get('doc_id')} "
                f"chunk_index={metadata.get('chunk_index')} "
                f"relevant={preliminary['per_chunk_relevant'][rank - 1]}"
            )
            print(f"     {preview}")

        answer = agent.answer(
            case.query,
            top_k=3,
            metadata_filter=case.metadata_filter,
        )
        evaluation = evaluate_results(case, results, answer=answer)
        if evaluation["coverage"] > 0:
            evidence_hits += 1
        total_rubric_score += evaluation["rubric_score"]
        answer_preview = " ".join(answer.split())[:500]
        print(f"Agent answer: {answer_preview}...")
        print(f"Expected document rank: {expected_rank or 'not in top-3'}")
        print(
            "Evidence coverage: "
            f"{evaluation['matched_groups']}/{evaluation['total_groups']} "
            f"({evaluation['coverage']:.0%}); "
            f"first relevant rank={evaluation['first_relevant_rank']}; "
            f"answer complete={evaluation['answer_complete']}; "
            f"rubric score={evaluation['rubric_score']}/2"
        )

        if case.metadata_filter:
            unfiltered = store.search(case.query, top_k=3)
            unfiltered_eval = evaluate_results(case, unfiltered)
            filtered_ids = [result["metadata"].get("doc_id") for result in results]
            unfiltered_ids = [result["metadata"].get("doc_id") for result in unfiltered]
            print(
                "A/B filter: "
                f"filtered evidence={evaluation['coverage']:.0%}, docs={filtered_ids}; "
                f"unfiltered evidence={unfiltered_eval['coverage']:.0%}, docs={unfiltered_ids}; "
                f"same_results={filtered_ids == unfiltered_ids}"
            )

    print(f"\nExpected document in top-3: {expected_doc_hits}/{len(BENCHMARK_CASES)}")
    print(f"At least one evidence marker in top-3: {evidence_hits}/{len(BENCHMARK_CASES)}")
    print(f"Strict rubric score: {total_rubric_score}/{len(BENCHMARK_CASES) * 2}")


if __name__ == "__main__":
    run_benchmark()

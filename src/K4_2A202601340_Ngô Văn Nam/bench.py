"""Benchmark cá nhân của Ngô Văn Nam.

Chạy từ thư mục gốc:
    python -m "src.K4_2A202601340_Ngô Văn Nam.bench"

Benchmark cố định corpus, 5 query và MockEmbedder; biến cá nhân duy nhất là
FixedSizeChunker(chunk_size=800, overlap=120).
"""
from __future__ import annotations

import re
import unicodedata
from pathlib import Path

from ingest import chunk_document, load_documents

from .agent import KnowledgeBaseAgent
from .benchmark_queries import BENCHMARK_CASES, BenchmarkCase
from .chunking import FixedSizeChunker
from .personal_embeddings import PersonalMockEmbedder
from .store import EmbeddingStore


ROOT = Path(__file__).resolve().parents[2]
DATA_DIR = ROOT / "data" / "k4_ecommerce"
STRATEGY = FixedSizeChunker(chunk_size=800, overlap=120)


def _normalise(text: str) -> str:
    text = unicodedata.normalize("NFD", text.lower())
    text = "".join(char for char in text if unicodedata.category(char) != "Mn")
    return re.sub(r"\s+", " ", text).strip()


def _group_hit(text: str, variants: tuple[str, ...]) -> bool:
    normalised = _normalise(text)
    return any(_normalise(variant) in normalised for variant in variants)


def _evaluate(case: BenchmarkCase, results: list[dict]) -> tuple[list[bool], bool]:
    combined = "\n".join(item["content"] for item in results)
    coverage = [_group_hit(combined, group) for group in case.evidence_groups]
    return coverage, all(coverage)


def _preview_llm(prompt: str) -> str:
    """LLM giả để kiểm tra grounding mà không cần API key."""
    context = prompt.split("Context:\n", 1)[-1].split("\n\nQuestion:", 1)[0]
    first = context.split("\n\n[2]", 1)[0]
    return f"Trả lời từ context truy xuất: {first[:500]}"


def build_personal_store() -> EmbeddingStore:
    embedder = PersonalMockEmbedder()
    chunks = []
    for document in load_documents(DATA_DIR):
        chunks.extend(chunk_document(document, STRATEGY))
    store = EmbeddingStore("ngo_van_nam_benchmark", embedder)
    store.add_documents(chunks)
    return store


def main() -> int:
    store = build_personal_store()
    agent = KnowledgeBaseAgent(store, _preview_llm)
    print("=== BENCHMARK CÁ NHÂN: NGÔ VĂN NAM ===")
    print("Strategy: FixedSizeChunker(chunk_size=800, overlap=120)")
    print("Embedder: MockEmbedder (kiểm tra pipeline, không đại diện ngữ nghĩa)")
    print(f"Corpus: {DATA_DIR}")
    print(f"Số chunks: {store.get_collection_size()}\n")

    hit_count = 0
    for index, case in enumerate(BENCHMARK_CASES, 1):
        if case.metadata_filter:
            results = store.search_with_filter(case.query, 3, case.metadata_filter)
        else:
            results = store.search(case.query, 3)
        coverage, hit = _evaluate(case, results)
        hit_count += int(hit)
        print(f"{index}. {case.query}")
        print(f"   filter={case.metadata_filter}; expected={case.expected_doc_id} ({case.expected_section})")
        for rank, item in enumerate(results, 1):
            meta = item["metadata"]
            relevant = any(_group_hit(item["content"], group) for group in case.evidence_groups)
            preview = " ".join(item["content"].split())[:190]
            print(
                f"   top{rank}: score={item['score']:.6f}; doc={meta.get('doc_id')}; "
                f"chunk={meta.get('chunk_index')}; relevant={relevant}; content={preview}"
            )
        print(f"   evidence={sum(coverage)}/{len(coverage)}; Hit@3={hit}")
        print(f"   agent={agent.answer(case.query, top_k=3, metadata_filter=case.metadata_filter)[:300]}\n")

    print(f"SUMMARY: Evidence Hit@3 = {hit_count}/5")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

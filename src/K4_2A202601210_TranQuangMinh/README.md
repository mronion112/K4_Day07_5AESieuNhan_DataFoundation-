# K4 — Trần Quang Minh (2A202601210)

Thư mục chứa các file code cá nhân cho Lab 7.

## Danh sách file

| File | Mô tả |
|---|---|
| `chunking.py` | SentenceChunker + RecursiveChunker + compute_similarity + ChunkingStrategyComparator |
| `store.py` | EmbeddingStore: 7 methods (add, search, search_with_filter, delete, etc.) |
| `agent.py` | KnowledgeBaseAgent: RAG pipeline (retrieve → prompt → LLM) |
| `bench.py` | Benchmark script: chạy 10 query với RecursiveChunker(500) + OpenAI embedder |
| `bench_detail.py` | Benchmark chi tiết: A/B filter test + snippet matching + scoring |
| `CHUNKING_ANALYSIS.md` | Phân tích 3 chiến lược chunking cho corpus chính sách TMĐT |

## Chiến lược cá nhân

**RecursiveChunker** với:
- `separators=["\n\n", "\n", ". ", " "]` — bỏ `""` (ký tự) để không cắt giữa từ
- `chunk_size=500` — cân bằng giữa ngữ cảnh và độ chi tiết
- Ưu tiên ranh giới tự nhiên: đoạn → dòng → câu → từ

## Kết quả benchmark

- Embedder: `text-embedding-3-small` (OpenAI)
- 534 chunks từ 6 tài liệu
- Điểm: 8/20 (theo snippet matching)
- Tốt: Q5 (vận chuyển), Q8 (trách nhiệm) — 2/2
- Thất bại: Q2 (phân mảnh penalty), Q3 (danh sách cấm), Q9 (nhầm thu thập/chia sẻ)

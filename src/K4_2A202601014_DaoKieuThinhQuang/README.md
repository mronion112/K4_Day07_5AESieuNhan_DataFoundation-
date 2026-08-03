# K4 — DaoKieuThinhQuang (2A202601014)

Thư mục chứa toàn bộ code và báo cáo cá nhân của Lab 7. Các file Python dùng chung ở `src/` không bị chỉnh sửa.

## Nội dung

| File | Vai trò |
|---|---|
| `chunking.py` | Ba chunker nền tảng, cosine similarity và comparator |
| `store.py` | Vector store in-memory: add, search, filter và delete |
| `agent.py` | RAG agent tạo context có `doc_id`, nguồn và số trích dẫn |
| `strategy.py` | Strategy riêng `HeadingRecursiveChunker(2000, overlap=300)` |
| `personal_embeddings.py` | Lexical hashing tiếng Việt: word + bigram + intent expansion |
| `benchmark_queries.py` | Đúng 5 query cố định, gold answer và evidence groups |
| `bench.py` | Baseline, top-3, chấm evidence, A/B filter và failure signal |
| `CHUNKING_ANALYSIS.md` | Phân tích định lượng/coherence của các strategy |
| `BENCHMARK_ANALYSIS.md` | Kết quả chunk-level và failure analysis cá nhân |
| `REPORT_CANHAN.md` | Báo cáo cá nhân theo rubric 60 điểm |

## Điểm khác biệt của strategy

`HeadingRecursiveChunker(chunk_size=2000, overlap=300)` tách văn bản chính sách theo Markdown heading hoặc mục đánh số ngắn. Heading không có body được gộp vào section kế tiếp thay vì trở thành record rỗng nội dung. Section dài được recursive split, có overlap, và tiêu đề được gắn lại vào từng mảnh con.

## Chạy lại

```bash
LAB_SOLUTION_PACKAGE=src.K4_2A202601014_DaoKieuThinhQuang \
  python -m pytest tests -v

python -m src.K4_2A202601014_DaoKieuThinhQuang.bench
```

Kết quả hiện tại: `42 passed`; benchmark lexical nạp 189 chunk và đạt 7/10 theo gold/evidence cố định trong `message.txt`. Có thể chạy lại mock bằng `EMBEDDING_PROVIDER=mock` để quan sát failure baseline.

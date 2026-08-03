# K4 — NgoVanNam (2A202601340)

Thư mục bài làm cá nhân của **Ngô Văn Nam**, nhóm **key coach chia**. Cấu trúc được trình bày đồng nhất với thư mục mẫu của thành viên Đào Kiều Thịnh Quang, nhưng toàn bộ cấu hình và số liệu bên dưới là kết quả của Ngô Văn Nam.

## Thành phần

| File | Vai trò |
|---|---|
| `chunking.py` | Ba chunker cơ bản và hàm cosine similarity |
| `store.py` | Vector store in-memory, filter và delete |
| `agent.py` | Nối retrieval với LLM và tạo nguồn `[1]`, `[2]`, ... |
| `strategy.py` | Thử nghiệm `HeadingSectionChunker` cho tài liệu chính sách |
| `personal_embeddings.py` | Khai báo embedder cá nhân dùng MockEmbedder |
| `benchmark_queries.py` | Đúng 5 query chung, gold answer và evidence bắt buộc |
| `bench.py` | Benchmark cá nhân có Top-3, score, metadata và Evidence Hit@3 |
| `CHUNKING_ANALYSIS.md` | So sánh bốn cấu hình chunking đã chạy |
| `BENCHMARK_ANALYSIS.md` | Phân tích retrieval, A/B filter và failure case |
| `REPORT_CANHAN.md` | Báo cáo cá nhân hoàn chỉnh |

## Strategy được chọn

Kết quả cá nhân chính dùng `FixedSizeChunker(chunk_size=800, overlap=120)`. Cấu hình này tạo **274 chunks** và đạt **Evidence Hit@3 = 2/5**, cao nhất trong bốn cấu hình đã đo bằng cùng MockEmbedder. `HeadingSectionChunker(800)` vẫn được giữ như một thử nghiệm domain-aware, nhưng chỉ đạt 0/5 với mock nên không được dùng làm kết quả cuối.

MockEmbedder chỉ kiểm tra pipeline deterministic, không biểu diễn ngữ nghĩa tiếng Việt. Vì vậy số liệu hiện tại không được dùng để kết luận mô hình embedding hay strategy nào tối ưu trong thực tế.

## Cách chạy

Từ thư mục gốc repository:

```powershell
$env:LAB_SOLUTION_PACKAGE="src.K4_2A202601340_Ngô Văn Nam"
python -m pytest tests -v
python -m "src.K4_2A202601340_Ngô Văn Nam.bench"
```

Kết quả đã ghi nhận: **42/42 tests passed**; benchmark cá nhân nạp **274 chunks**, Evidence Hit@3 **2/5**.

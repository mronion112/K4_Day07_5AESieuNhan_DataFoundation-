# Báo Cáo Cá Nhân — Lab 7: Embedding & Vector Store

**Họ tên:** DaoKieuThinhQuang  
**MSSV:** 2A202601014
**Nhóm:** 5AE Siêu Nhân  
**Ngày:** 03/08/2026

**Tổng điểm phần cá nhân: 60** = Khởi động (5) + Hướng tiếp cận (10) + Hoàn thiện code (30) + Dự đoán độ tương tự (5) + Kết quả truy xuất (10).

## 1. Khởi động (Warm-up)

### Độ tương tự cosine

Cosine similarity cao nghĩa là hai vector embedding hướng gần giống nhau, do đó hai đoạn văn thường có nội dung hoặc ý nghĩa tương tự dù cách dùng từ có thể khác nhau.

**Cặp tương đồng cao:**

- Câu A: “Khách hàng được hoàn tiền khi sản phẩm bị lỗi.”
- Câu B: “Người mua có thể nhận lại tiền nếu hàng hóa gặp khuyết điểm.”
- Hai câu dùng từ khác nhau nhưng cùng diễn đạt quyền hoàn tiền khi hàng bị lỗi.

**Cặp tương đồng thấp:**

- Câu A: “Đơn hàng sẽ được giao trong ba ngày.”
- Câu B: “Mạng nơ-ron học đặc trưng từ dữ liệu.”
- Hai câu thuộc hai chủ đề khác nhau: vận chuyển hàng hóa và học máy.

Cosine similarity tập trung vào hướng của vector nên ít bị ảnh hưởng bởi độ lớn của embedding. Khoảng cách Euclid còn phụ thuộc vào độ lớn, vì vậy hai vector cùng hướng nhưng có độ dài khác nhau vẫn có thể bị coi là xa nhau.

### Bài toán chunking

Với `length=10.000`, `chunk_size=500`, `overlap=50`:

```text
ceil((10.000 - 50) / (500 - 50))
= ceil(9.950 / 450)
= ceil(22,111...)
= 23 chunks
```

Khi tăng `overlap` lên 100:

```text
ceil((10.000 - 100) / (500 - 100))
= ceil(9.900 / 400)
= ceil(24,75)
= 25 chunks
```

Số chunk tăng từ 23 lên 25. Overlap lớn hơn giúp giữ ngữ cảnh nằm sát ranh giới giữa hai chunk, nhưng làm tăng lượng dữ liệu lưu trữ, chi phí embedding và khả năng kết quả truy xuất bị lặp.

## 2. Hướng tiếp cận của tôi (10 điểm)

### Chunking và similarity

- `SentenceChunker` tách tại khoảng trắng đứng sau `.`, `!` hoặc `?`, loại phần rỗng rồi nhóm tối đa số câu được cấu hình.
- `RecursiveChunker` ưu tiên ranh giới đoạn, dòng, câu và từ. Phần còn quá dài được xử lý bằng separator ưu tiên thấp hơn; khi hết separator, thuật toán cắt cố định theo `chunk_size`.
- `compute_similarity` dùng tích vô hướng chia cho tích hai chuẩn vector và trả `0.0` nếu một trong hai vector có độ dài bằng không.
- `ChunkingStrategyComparator` chạy ba chiến lược và trả số chunk, độ dài trung bình cùng danh sách chunk; trường hợp text rỗng có độ dài trung bình bằng `0.0`.

### Lưu trữ, truy xuất và trả lời có dẫn nguồn

#### EmbeddingStore

`EmbeddingStore` được triển khai bằng bộ nhớ trong để toàn bộ thao tác dùng chung một cấu trúc record gồm `id`, `content`, bản sao `metadata` và `embedding`. Khi thêm document, store bổ sung `doc_id` nếu metadata chưa có và ghép chỉ số tăng dần vào ID record để tránh trùng ID.

`search` tạo embedding của query đúng một lần, tính dot product với từng record, sắp xếp score giảm dần rồi lấy tối đa `top_k`. `search_with_filter` lọc metadata **trước khi** xếp hạng; nếu lấy top-k trước rồi mới lọc thì các record không phù hợp có thể chiếm hết top-k và làm mất tài liệu hợp lệ ở phía sau.

`delete_document` loại tất cả chunk có cùng `metadata["doc_id"]`. Hàm trả `True` khi kích thước store giảm và `False` khi không tìm thấy document cần xóa.

#### KnowledgeBaseAgent

`KnowledgeBaseAgent.answer` gọi store để lấy top-k chunk, đánh số từng chunk và đưa cả `doc_id` lẫn nguồn vào context. Prompt yêu cầu LLM chỉ dùng context, trích dẫn bằng `[1]`, `[2]`, ... và nói rõ khi dữ liệu không đủ. Nếu store rỗng, agent trả thông báo trực tiếp mà không gọi LLM.

## 3. Hoàn thiện code (30 điểm)

### Kết quả kiểm thử

Chạy test với package cá nhân:

```bash
LAB_SOLUTION_PACKAGE=src.K4_2A202601014_DaoKieuThinhQuang \
  python -m pytest tests -v
```

Kết quả:

```text
============================== 42 passed in 0.04s ==============================
```

**Số lượng test vượt qua:** 42 / 42.

Smoke test RAG trên 6 tài liệu trong `data/k4_ecommerce` chạy thành công. Agent tạo context có đánh số `[1]` và thông tin nguồn để truy vết.

## 4. Dự đoán độ tương tự (5 điểm)

| Cặp | Câu A | Câu B | Dự đoán | Điểm mock thực tế | Đúng? |
|---|---|---|---|---:|---|
| 1 | Khách hàng được hoàn tiền khi sản phẩm bị lỗi | Người mua nhận lại tiền nếu hàng có khuyết điểm | Cao | -0,1098 | Không |
| 2 | Đơn hàng giao trong ba ngày | Mạng nơ-ron học đặc trưng từ dữ liệu | Thấp | -0,0632 | Có |
| 3 | Shopee bảo vệ dữ liệu cá nhân | Nền tảng đảm bảo quyền riêng tư khách hàng | Cao | 0,1268 | Không rõ/thấp |
| 4 | Shopee thu thập dữ liệu cá nhân | Shopee chia sẻ dữ liệu với bên thứ ba | Cao vừa | 0,0224 | Không |
| 5 | Người bán đóng gói đúng quy cách | Người mua yêu cầu trả hàng/hoàn tiền | Thấp | 0,3016 | Không |

Kết quả bất ngờ nhất là cặp 1: hai câu gần như cùng nghĩa nhưng điểm âm, trong khi cặp 5 khác hành động lại có điểm cao nhất. Nguyên nhân là `MockEmbedder` tạo vector xác định theo toàn chuỗi chứ không học ngữ nghĩa. Bảng này kiểm được công thức cosine và tính reproducible, nhưng không thể dùng để đánh giá khả năng hiểu tiếng Việt của embedding.

## 5. Kết quả truy xuất và strategy riêng (10 điểm)

### Bộ 5 benchmark query cố định

Bộ câu hỏi và gold answer được giữ nguyên theo `message.txt` trước khi đánh giá strategy. Chi tiết gồm gold answer, document, section và evidence groups kỳ vọng nằm trong `benchmark_queries.py`. Nếu gold không khớp corpus thì kết quả được ghi là failure, không sửa gold theo output retrieval.

| # | Dạng câu hỏi | Document kỳ vọng | Filter |
|---|---|---|---|
| 1 | Số lượng + quy trình/phí trả hàng | `tra-hang-phuong-thuc-gui-hoan-tra`, mục 1.1 và 2.2 | `customer_role=buyer` |
| 2 | Điều kiện/chế tài vi phạm | `chinh-sach-cam-han-che-san-pham`, mục 3 | `customer_role=seller` |
| 3 | Liệt kê nội dung/sản phẩm cấm | `quy-dinh-dang-ban-san-pham`, mục B.2 | `customer_role=seller` |
| 4 | Trường hợp thu thập dữ liệu cá nhân | `chinh-sach-bao-mat`, mục 2 | Không |
| 5 | Ngoại lệ hàng không hỗ trợ vận chuyển | `chinh-sach-van-chuyen-shopee`, mục B | Không |

### Baseline trên 3 tài liệu

`ingest.load_documents()` đã loại YAML front matter trước khi gọi comparator. Tất cả baseline dùng `chunk_size=400`.

| Tài liệu | Strategy | Số chunk | Độ dài trung bình |
|---|---:|---:|---:|
| Trả hàng/phương thức hoàn trả | Fixed size | 15 | 380,73 |
|  | By sentences | 9 | 632,67 |
|  | Recursive | 18 | 315,39 |
| Chính sách cấm/hạn chế sản phẩm | Fixed size | 26 | 385,85 |
|  | By sentences | 47 | 211,36 |
|  | Recursive | 31 | 321,68 |
| Chính sách bảo mật | Fixed size | 108 | 396,73 |
|  | By sentences | 65 | 657,34 |
|  | Recursive | 166 | 256,58 |

Sentence chunking có độ dài trung bình vượt 400 ở hai tài liệu vì giới hạn của strategy này là số câu, không phải số ký tự. Recursive tạo nhiều chunk hơn nhưng giữ các chunk gần giới hạn kích thước tốt hơn.

### Strategy cá nhân: HeadingRecursiveChunker

Corpus chính sách được biên soạn theo tiêu đề và các mục đánh số, nên strategy tách tại heading trước để mỗi chunk tập trung vào một điều khoản. Bản đầu `chunk_size=400` sinh quá nhiều fragment/heading-only record. Bản tune cuối dùng `chunk_size=2000`, `overlap=300`: heading rỗng được gộp vào section kế tiếp, section dài được recursive split và giữ overlap cùng tiêu đề.

Chạy benchmark:

```bash
python -m src.K4_2A202601014_DaoKieuThinhQuang.bench
```

Kết quả benchmark cải tiến:

- Strategy: `HeadingRecursiveChunker(chunk_size=2000, overlap=300)`.
- Embedder: `VietnameseLexicalEmbedder` — chuẩn hóa dấu, word/bigram hashing và intent expansion tổng quát. Đây là lexical baseline minh bạch, không phải neural semantic model.
- Nạp 189 chunk từ 6 tài liệu; max 1.997 ký tự.
- In strategy, tham số, filter, gold answer, top-3 score/doc_id/chunk preview và agent answer cho đủ 5 query.
- Document kỳ vọng đứng top-1 ở 5/5 query.
- Có evidence trong top-3 ở 4/5 query; Q3 đạt 4/5 nhóm và Q5 đạt 0/8 nhóm.
- Strict chunk-level rubric: 7/10; offline agent trả nguyên evidence top-3 có citation và không sinh thêm dữ kiện.

Mock baseline trước cải tiến chỉ đạt 1/10 dù `doc_id` đạt 5/5. Điều này giúp phát hiện lỗi chấm theo tài liệu thay vì chunk. Lần chạy lexical cuối giữ nguyên corpus, 5 query, gold và evidence groups trong lúc tune. Muốn so sánh công bằng giữa thành viên, mọi người vẫn phải chạy lại bằng cùng một backend.

### Bảng kết quả cá nhân

| # | Top-1 tóm tắt | Score | Evidence trong top-3 | Agent answer | Điểm |
|---|---|---:|---:|---|---:|
| 1 | Đúng section hình thức/phí trả hàng | 0,3549 | 5/5 (100%) | Evidence extractive đủ, có citation | 2/2 |
| 2 | Đúng mục 3 — chế tài vi phạm | 0,3276 | 5/5 | Đủ danh sách chế tài | 2/2 |
| 3 | Đúng mục B.2 — nội dung cấm | 0,2132 | 4/5 (80%) | Thiếu một nhóm gold | 1/2 |
| 4 | Đúng mục 2 — khi thu thập dữ liệu | 0,2318 | 4/4 | Context kết hợp đủ các trường hợp | 2/2 |
| 5 | Đúng mục B nhưng corpus không có gold | 0,4917 | 0/8 | Không thể trả đủ gold từ context | 0/2 |

### A/B filter và failure case

Q1 có và không filter đều đạt 100% vì query đã rất đặc hiệu. Q2 giữ 100% nhưng filter thay top-2/3 bằng tài liệu đúng đối tượng seller. Q3 giữ coverage 80% ở cả hai lần, song filter đưa tài liệu đăng bán lên top-1 thay vì để điều khoản dịch vụ chiếm vị trí đầu. Filter cải thiện precision/rank nhưng không phải lúc nào cũng đổi coverage.

Failure ban đầu rõ nhất là Q2: mock đưa đúng `doc_id` nhưng top-1 nói về thực vật/động vật thay vì mục 3. Sau khi bỏ heading-only record, tăng context/overlap và dùng lexical embedding, Q2 đạt 5/5 marker ở top-1. Failure cuối cùng là Q5: top-1 đúng document/mục B nhưng không có bằng chứng cho 8 nhóm trong gold cố định. Corpus hiện tại liệt kê nhóm hàng khác, nên Q5 được chấm 0/2 thay vì sửa gold.

Chi tiết top-3, provenance, A/B và failure gold–corpus được lưu trong `BENCHMARK_ANALYSIS.md`.

## Tự đánh giá

| Tiêu chí | Điểm tạm tự đánh giá |
|---|---:|
| Khởi động | 5 / 5 |
| Hướng tiếp cận | 10 / 10 |
| Hoàn thiện code | 30 / 30 |
| Dự đoán độ tương tự | 5 / 5 |
| Kết quả truy xuất hiện tại | 7 / 10 |
| **Tổng** | **57 / 60** |

Điểm retrieval là kết quả của lần chạy lexical strict evidence. Khi nhóm thống nhất backend chung, cần chạy lại đúng 5 query mà không thay query/gold/evidence groups để có bảng so sánh công bằng giữa thành viên.

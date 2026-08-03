# Báo Cáo Cá Nhân — Lab 7: Embedding & Vector Store

**Họ tên:** Ngô Văn Nam  
**MSS:** 2A202601340  
**Nhóm:** key coach chia  
**Ngày:** 03/08/2026

> Benchmark hiện dùng MockEmbedder deterministic để kiểm tra pipeline. Mock không biểu diễn ngữ nghĩa tiếng Việt, vì vậy các điểm retrieval dưới đây là kết quả checkpoint, không phải kết luận chất lượng mô hình.

---

## 1. Khởi động (Warm-up) — 5 điểm

### Cosine similarity

Cosine similarity cao nghĩa là hai vector có hướng gần nhau; với embedding ngữ nghĩa, điều đó thường biểu thị nội dung gần nghĩa dù cách dùng từ khác nhau.

- Ví dụ cao: “Người mua được yêu cầu trả hàng” và “Khách hàng có thể hoàn trả sản phẩm”.
- Ví dụ thấp: “Người mua yêu cầu hoàn tiền” và “Trời hôm nay có mưa lớn”.

Cosine phù hợp hơn Euclid cho text embedding vì tập trung vào hướng vector, ít bị ảnh hưởng bởi độ lớn vector.

### Tính số chunk

Tài liệu 10.000 ký tự, size 500, overlap 50:

```text
ceil((10.000 - 50) / (500 - 50)) = 23 chunks
```

Nếu overlap tăng lên 100:

```text
ceil((10.000 - 100) / (500 - 100)) = 25 chunks
```

Overlap lớn giữ thêm ngữ cảnh ở biên nhưng tăng dữ liệu trùng, dung lượng và chi phí xử lý.

---

## 2. Hướng tiếp cận của tôi — 10 điểm

### Chunking

- `FixedSizeChunker`: cắt theo cửa sổ ký tự, bước nhảy bằng `chunk_size - overlap`.
- `SentenceChunker`: nhận diện ranh giới `.`, `!`, `?` rồi gom tối đa số câu được cấu hình.
- `RecursiveChunker`: ưu tiên đoạn, dòng, câu, từ rồi mới cắt cứng theo ký tự.
- `HeadingSectionChunker`: tách theo heading/điều khoản, section dài được recursive và gắn lại heading vào từng mảnh.

Sau khi so sánh cùng corpus/query/embedder, tôi chọn `FixedSizeChunker(800, overlap=120)` vì đạt Evidence Hit@3 tốt nhất: 2/5. Phân tích đầy đủ nằm tại `CHUNKING_ANALYSIS.md`.

### EmbeddingStore

Mỗi record gồm ID duy nhất, content, bản sao metadata và embedding. Query chỉ được embed một lần; store tính dot product, sắp xếp score giảm dần rồi lấy Top-k. `search_with_filter` lọc metadata trước khi rank. `delete_document` xóa mọi chunk có cùng `metadata['doc_id']`.

### KnowledgeBaseAgent

Agent retrieve Top-k, đánh số context `[1]`, `[2]`, kèm `doc_id` và nguồn. Prompt yêu cầu chỉ dùng context, nêu rõ khi thiếu thông tin và dẫn nguồn. Store rỗng thì không gọi LLM.

---

## 3. Hoàn thiện code — 30 điểm

Lệnh kiểm tra:

```powershell
$env:LAB_SOLUTION_PACKAGE="src.K4_2A202601340_Ngô Văn Nam"
python -m pytest tests -v
```

Kết quả ghi nhận bằng Python 3.13.14, pytest 9.1.1:

```text
42 passed, 1 warning in 0.05s
```

**Số test vượt qua: 42/42.** Public interface được giữ nguyên và không còn `NotImplementedError` trong phần cá nhân.

---

## 4. Dự đoán độ tương tự — 5 điểm

| # | Cặp câu (tóm tắt) | Dự đoán | Score thực tế |
|---|---|---|---:|
| 1 | trả lại sản phẩm ↔ hoàn trả hàng hóa | Cao | -0,163796 |
| 2 | mô tả chính xác ↔ thông tin đúng | Cao | 0,098358 |
| 3 | bằng chứng đổi trả ↔ chứng từ hoàn hàng | Cao | -0,114241 |
| 4 | hàng cấm ↔ sản phẩm giảm giá | Thấp | -0,179067 |
| 5 | hoàn tiền ↔ trời mưa | Thấp | 0,106350 |

Bất ngờ nhất là cặp 5 không liên quan lại có score mock cao nhất, còn cặp 1 gần nghĩa nhận điểm âm. Kết quả này xác nhận MockEmbedder chỉ deterministic, không thể dùng để đánh giá ngữ nghĩa.

---

## 5. Kết quả truy xuất cá nhân — 10 điểm

Thiết lập: `FixedSizeChunker(800, overlap=120)`, MockEmbedder, **274 chunks từ 6 tài liệu**, đúng 5 query chung của nhóm.

| # | Query | Top-1 (tóm tắt) | Score | Đánh giá |
|---|---|---|---:|---|
| 1 | Hình thức và phí trả hàng | `tra-hang...::chunk_3`, đổi phương thức lấy hàng | 0,230391 | Đủ evidence khi gộp Top-3, Top-1 thiếu |
| 2 | Chế tài hàng cấm/hạn chế | `quy-dinh-dang-ban...::chunk_9`, mô tả/khuyến mãi | 0,284884 | Sai section, thiếu evidence |
| 3 | Khi Shopee thu thập dữ liệu | `dieu-khoan-dich-vu::chunk_41`, sở hữu trí tuệ | 0,427944 | Không liên quan |
| 4 | Hàng không hỗ trợ vận chuyển | `chinh-sach-bao-mat::chunk_19`, cookie | 0,345976 | Top-1 sai; evidence đủ trong Top-3 |
| 5 | Ngoại lệ người bán tự vận chuyển | `dieu-khoan-dich-vu::chunk_65`, tài khoản đảm bảo | 0,469247 | Không liên quan |

**Evidence Hit@3: 2/5; điểm tạm theo rubric: 2/10.** Chi tiết Top-3, A/B filter và failure case nằm trong `BENCHMARK_ANALYSIS.md`.

### A/B filter

- Query 1: filter `buyer` cải thiện từ miss thành hit.
- Query 2: filter `seller` đổi thứ hạng nhưng vẫn miss; đúng vai trò không bảo đảm đúng section.

### Failure case

Ở query 2, cả ba chunk đầu đều không chứa các chế tài dù Top-3 có một chunk thuộc đúng tài liệu gold. Điều này cho thấy chỉ kiểm tra `doc_id` sẽ đánh giá quá cao. Cần chấm chuỗi evidence trong nội dung; sau đó thử multilingual embedding và thêm `section_title` vào text embedding.

---

## Tự đánh giá

| Tiêu chí | Điểm |
|---|---:|
| Warm-up | 5/5 |
| Hướng tiếp cận | 10/10 |
| Core implementation | 30/30 |
| Similarity predictions | 2/5 |
| Competition results | 2/10 |
| **Tổng hiện tại** | **49/60** |

## Việc cần bổ sung trước khi nộp

1. Nếu môi trường cho phép, chạy lại đúng benchmark bằng local multilingual embedding.
2. Sau demo, bổ sung bài học cụ thể từ thành viên/nhóm khác.
3. Kiểm tra `.env`, `.venv`, database/cache local không nằm trong commit.

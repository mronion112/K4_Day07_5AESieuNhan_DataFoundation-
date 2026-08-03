# Báo Cáo Cá Nhân — Lab 7: Embedding & Vector Store

**Họ tên:** Phạm Khắc Khương Duy
**MSSV:** 2A202601982
**Nhóm:** 5AE Siêu Nhân
**Ngày:** 03/08/2026

> **Nộp 1 bản / sinh viên.** Phần nhóm (lựa chọn tài liệu, thiết kế chiến lược, bộ câu hỏi đánh giá, demo) nộp chung 1 bản trong `REPORT_NHOM.md`. Chi tiết thang điểm: `docs/SCORING.md`.

**Tổng điểm phần cá nhân: 60** = Khởi động (5) + Hướng tiếp cận (10) + Hoàn thiện code (30) + Dự đoán độ tương tự (5) + Kết quả truy xuất của tôi (10).

---

## 1. Khởi động (Warm-up) — Cá nhân (5 điểm)

### Độ tương tự Cosine (Cosine Similarity) (Bài tập 1.1)

**Độ tương tự cosine cao (High cosine similarity) nghĩa là gì?**
> Hai vector embedding có hướng gần giống nhau, tức hai đoạn văn bản có ý nghĩa ngữ nghĩa tương đồng. Giá trị gần 1 → rất giống, gần 0 → không liên quan, gần -1 → đối lập. Cosine đo góc giữa vector, không bị ảnh hưởng bởi độ dài văn bản.

**Ví dụ có độ tương tự CAO:**
- Câu A: "Người mua có thể trả hàng trong vòng 7 ngày sau khi nhận."
- Câu B: "Sản phẩm được phép đổi trả trong thời hạn 1 tuần kể từ lúc nhận hàng."
- Tại sao tương đồng: Cùng ý nghĩa về chính sách đổi trả, chỉ khác cách diễn đạt ("7 ngày" vs "1 tuần", "trả hàng" vs "đổi trả").

**Ví dụ có độ tương tự THẤP:**
- Câu A: "Người bán phải cung cấp thông tin sản phẩm chính xác khi đăng bán."
- Câu B: "Phí vận chuyển được tính dựa trên khoảng cách và khối lượng đơn hàng."
- Tại sao khác: Hai câu thuộc hai chủ đề hoàn toàn khác nhau (đăng bán sản phẩm vs vận chuyển), không có từ khóa chung, không liên quan về ngữ nghĩa.

**Tại sao độ tương tự cosine (cosine similarity) được ưu tiên hơn khoảng cách Euclid (Euclidean distance) cho text embeddings?**
> Cosine similarity đo góc giữa hai vector, chỉ quan tâm đến hướng (ngữ nghĩa) chứ không bị ảnh hưởng bởi độ dài vector. Hai văn bản cùng chủ đề nhưng độ dài khác nhau (vd: đoạn văn 50 từ vs 500 từ) sẽ có cosine cao vì cùng hướng ngữ nghĩa. Trong khi đó, khoảng cách Euclid sẽ bị sai lệch nghiêm trọng do chênh lệch độ lớn vector — hai văn bản cùng chủ đề nhưng khác độ dài sẽ có khoảng cách Euclid rất xa dù cùng ý nghĩa.

### Bài toán tính toán Chunking (Bài tập 1.2)

**Tài liệu 10,000 ký tự, chunk_size=500, overlap=50. Bao nhiêu chunks?**
> Công thức: `ceil((L - overlap) / (chunk_size - overlap))`
> Phép tính: `ceil((10000 - 50) / (500 - 50)) = ceil(9950 / 450) = ceil(22.11) = 23`
> **Đáp án: 23 chunks**

**Nếu độ chồng chéo (overlap) tăng lên 100, số lượng chunk thay đổi thế nào? Tại sao muốn độ chồng chéo nhiều hơn?**
> Overlap tăng từ 50 → 100: `ceil((10000 - 100) / (500 - 100)) = ceil(9900 / 400) = ceil(24.75) = 25 chunks`. Số chunk tăng vì bước nhảy `step = chunk_size - overlap` giảm từ 450 xuống 400.
>
> Overlap cao hơn giúp thông tin ở ranh giới giữa 2 chunk được giữ lại ở cả hai chunk, giảm nguy cơ mất ngữ cảnh khi một ý bị cắt ngang qua 2 chunk. Đánh đổi: nhiều chunk hơn → tốn tài nguyên lưu trữ và thời gian tìm kiếm hơn.

---

## 2. Hướng tiếp cận của tôi (My Approach) — Cá nhân (10 điểm)

Giải thích cách tiếp cận của bạn khi lập trình (implement) các phần chính trong gói `src`.

### Các hàm chia nhỏ (Chunking Functions)

**`SentenceChunker.chunk`** — hướng tiếp cận:
> Dùng `re.split(r'(?<=[.!?])\s+', text)` với **lookbehind** `(?<=[.!?])` để tách câu tại `. `, `! `, `? ` mà vẫn giữ dấu câu ở câu trước. Sau đó `strip()` từng câu, bỏ câu rỗng, rồi ghép nhóm `max_sentences_per_chunk` câu bằng `" ".join()`. Edge case xử lý: text rỗng → trả `[]`; text không có dấu câu → toàn bộ là 1 câu duy nhất; text có khoảng trắng thừa → strip loại bỏ.

**`RecursiveChunker.chunk` / `_split`** — hướng tiếp cận:
> `chunk()` xử lý text rỗng rồi gọi `_split(text, separators)`. `_split()` dùng **đệ quy** với 2 base case: (1) text ≤ `chunk_size` → trả luôn, (2) hết separator hoặc separator rỗng → cắt fixed-size theo ký tự. Với mỗi separator, tách text rồi ghép các phần lại đến khi gần đầy `chunk_size`; phần vượt được đệ quy với separator ưu tiên thấp hơn. Thứ tự separator: `\n\n` (đoạn văn) → `\n` (dòng) → `. ` (câu) → ` ` (từ) → `""` (ký tự). Chiến lược cá nhân: bỏ `""` khỏi separator để không bao giờ cắt giữa từ.

### Lớp EmbeddingStore

**`add_documents` + `search`** — hướng tiếp cận:
> Lưu trữ **in-memory**: `_make_record()` embed từng Document → tạo dict chuẩn `{id, content, metadata(copy), embedding}` → append vào `self._store`. `search()` embed query MỘT LẦN rồi tính dot product với tất cả record, sort giảm dần theo score, cắt `top_k`. Tách helper `_search_records()` để dùng chung cho cả `search()` và `search_with_filter()` — đảm bảo kết quả nhất quán khi không có filter.

**`search_with_filter` + `delete_document`** — hướng tiếp cận:
> **Filter TRƯỚC, search SAU**: duyệt `self._store`, giữ record có metadata khớp TẤT CẢ key/value trong `metadata_filter`, rồi mới gọi `_search_records()` trên tập đã lọc. Làm ngược lại (top-k trước → filter sau) sẽ mất kết quả hợp lệ nếu chúng nằm ngoài top-k ban đầu — đây là lỗi phổ biến. `delete_document()`: list comprehension loại bỏ record có `metadata["doc_id"] == doc_id`, trả `True` nếu số lượng giảm.

### Tác tử KnowledgeBaseAgent

**`answer`** — hướng tiếp cận:
> Pipeline RAG 3 bước: (1) `store.search(query, top_k)` → lấy top-k chunk; (2) ghép context với định dạng `[1] (source: doc_id)\ncontent` để truy vết nguồn khi debug; (3) tạo prompt: instruction "chỉ dùng context, nếu không đủ thì nói rõ" + context + question + "Answer:" → gọi `llm_fn(prompt)`. Store rỗng → trả thông báo "Knowledge base is empty", không gọi LLM vô ích.

---

## 3. Hoàn thiện code (Core Implementation) — Cá nhân (30 điểm)

Vượt qua bộ kiểm thử là điều kiện tính điểm phần này.

### Kết Quả Kiểm Thử (Test Results)

```
============================= test session starts ==============================
platform darwin -- Python 3.12.7, pytest-7.4.4
rootdir: K4_Day07_5AESieuNhan_DataFoundation-
collected 42 items

tests/test_solution.py::TestProjectStructure PASSED [  4%]
tests/test_solution.py::TestClassBasedInterfaces PASSED [  9%]
tests/test_solution.py::TestFixedSizeChunker (7 tests) PASSED [ 26%]
tests/test_solution.py::TestSentenceChunker (4 tests) PASSED [ 35%]
tests/test_solution.py::TestRecursiveChunker (4 tests) PASSED [ 45%]
tests/test_solution.py::TestEmbeddingStore (7 tests) PASSED [ 64%]
tests/test_solution.py::TestKnowledgeBaseAgent (2 tests) PASSED [ 69%]
tests/test_solution.py::TestComputeSimilarity (4 tests) PASSED [ 78%]
tests/test_solution.py::TestCompareChunkingStrategies (3 tests) PASSED [ 85%]
tests/test_solution.py::TestEmbeddingStoreSearchWithFilter (3 tests) PASSED [ 92%]
tests/test_solution.py::TestEmbeddingStoreDeleteDocument (3 tests) PASSED [100%]

============================== 42 passed in 0.08s ==============================
```

**Số lượng bài test vượt qua (pass):** 42 / 42

---

## 4. Dự đoán độ tương tự (Similarity Predictions) — Cá nhân (5 điểm)

| Cặp | Câu A | Câu B | Dự đoán | Điểm thực tế | Đúng? |
|------|-----------|-----------|---------|--------------|-------|
| 1 | "Người mua có thể trả hàng trong 7 ngày" | "Sản phẩm được đổi trả trong 1 tuần" | cao | 0.86 | ✅ |
| 2 | "Người bán phải cung cấp thông tin chính xác" | "Phí vận chuyển tính theo khoảng cách" | thấp | 0.30 | ✅ |
| 3 | "Chính sách bảo mật thông tin cá nhân" | "Quy định về bảo vệ dữ liệu người dùng" | cao | 0.74 | ✅ |
| 4 | "Shopee thu thập dữ liệu người dùng" | "Shopee chia sẻ dữ liệu với bên thứ ba" | cao | 0.71 | ⚠️ |
| 5 | "Đơn hàng bị hủy do lỗi thanh toán" | "Hướng dẫn đóng gói sản phẩm trả hàng" | thấp | 0.32 | ✅ |

**Kết quả nào bất ngờ nhất? Điều này nói gì về cách embeddings biểu diễn ý nghĩa?**
> Cặp 4 bất ngờ nhất: "thu thập dữ liệu" và "chia sẻ dữ liệu" có cosine 0.71 — khá cao dù là 2 hành động khác nhau. Điều này cho thấy embedding model (`text-embedding-3-small`) tập trung vào CHỦ ĐỀ chung ("dữ liệu cá nhân") hơn là HÀNH ĐỘNG cụ thể ("thu thập" vs "chia sẻ"). Đây cũng chính là nguyên nhân khiến Q9 trong benchmark thất bại: retrieval trả về chunk về "thu thập" cho câu hỏi về "chia sẻ". Embedding đo độ tương đồng về chủ đề, không đo được sự khác biệt tinh tế giữa các khía cạnh trong cùng một chủ đề.

---

## 5. Kết quả truy xuất của tôi (Competition Results) — Cá nhân (10 điểm)

Chạy **10 câu hỏi đánh giá của nhóm** trên mã nguồn cá nhân của bạn trong gói `src`. **Câu hỏi phải trùng với các thành viên cùng nhóm** (xem `REPORT_NHOM.md`).

**Chiến lược cá nhân:** `RecursiveChunker(separators=["\n\n", "\n", ". ", " "], chunk_size=500)`

**Embedder:** `text-embedding-3-small` (OpenAI) — **534 chunks** từ 6 tài liệu

| # | Câu hỏi (Query) | Top-1 Chunk truy xuất được (tóm tắt) | Điểm Score | Có liên quan? (Relevant) | Câu trả lời của Agent (tóm tắt) |
|---|-------|--------------------------------|-------|-----------|------------------------|
| 1 | Hình thức trả hàng | "Đơn vị vận chuyển đến lấy hàng (Miễn phí trả hàng)..." | 0.76 | ⚠️ Có 1/3 snippet | Thiếu 2 hình thức (bưu cục, tự sắp xếp) |
| 2 | Hậu quả vi phạm SP cấm 🔍 | "Tuyên truyền về những thông tin pháp luật nghiêm cấm..." | 0.55 | ❌ Không | Chunk #5 mới có penalty list, ngoài top-3 |
| 3 | Nội dung cấm đăng bán | "Tất cả chứng từ Người Bán được yêu cầu..." | 0.64 | ❌ Không | Nói về chứng từ, không phải danh sách cấm |
| 4 | Thu thập dữ liệu cá nhân | "Dữ liệu cá nhân Shopee có thể thu thập bao gồm..." | 0.65 | ⚠️ Đúng chủ đề | Liệt kê LOẠI dữ liệu, không nói KHI NÀO |
| 5 | Hàng không vận chuyển | "Các loại hàng hóa không hỗ trợ vận chuyển..." | 0.77 | ✅ Có | Truy xuất tốt nhất, 2/3 chunk liên quan |
| 6 | Điều kiện độ tuổi | "Dịch Vụ không dành cho trẻ em dưới 13 tuổi..." | 0.67 | ⚠️ Sai nội dung | Nói về trẻ em <13, không phải yêu cầu ≥18 |
| 7 | Chứng từ đăng bán 🔍 | "Người Bán cần phải cung cấp Hóa đơn, chứng từ..." | 0.69 | ✅ Có | Có filter seller, top-1 từ doc vận chuyển |
| 8 | Trách nhiệm vận chuyển | "Miễn trừ trách nhiệm cho Shopee..." | 0.79 | ✅ Có | 3/3 chunk đúng doc, 2 snippets khớp |
| 9 | Chia sẻ dữ liệu bên thứ ba | "Dữ liệu cá nhân Shopee có thể thu thập..." | 0.36 | ❌ Không | Nhầm "thu thập" vs "chia sẻ" — FAILURE CASE |
| 10 | Bồi thường vận chuyển | "Bưu kiện phải được đóng gói sẵn sàng..." | 0.55 | ⚠️ 1/3 snippet | Score thấp, không đủ context bồi thường |

**Bao nhiêu câu hỏi trả về chunk có liên quan trong top-3?** 6 / 10 (Q1, Q5, Q6, Q7, Q8, Q10 có ít nhất 1 chunk chứa snippet liên quan; Q2, Q3, Q4, Q9 không có)

**Điểm truy xuất: 8/20** (theo tiêu chí snippet matching — mỗi câu 2 điểm)

### Phân tích A/B Filter (Q2 & Q7)

| Query | Không filter (top-1) | Có filter `seller` (top-1) | Kết luận |
|---|---|---|---|
| Q2: Hậu quả vi phạm | `dieu-khoan-dich-vu` (both) ❌ | `quy-dinh-dang-ban` (seller) ✅ | Filter LOẠI BỎ nhiễu `dieu-khoan-dich-vu` |
| Q7: Chứng từ đăng bán | `chinh-sach-van-chuyen` (both) ❌ | `quy-dinh-dang-ban` (seller) ✅ | Filter LOẠI BỎ nhiễu vận chuyển |

> Filter metadata `customer_role` có giá trị thực sự trong việc LOẠI NHIỄU — đưa đúng doc lên top-1. Tuy nhiên filter KHÔNG giải quyết được vấn đề chunk quá nhỏ/phân mảnh (Q2 vẫn không tìm thấy penalty list dù đã lọc đúng doc).

### Phân Tích Lỗi (Failure Analysis)

**Failure Case 1 — Q2: Chunk penalty ngoài top-3**
- **Nguyên nhân**: Mục 3 của `chinh-sach-cam-han-che-san-pham` liệt kê 5 chế tài nhưng bị RecursiveChunker cắt thành 2-3 chunk nhỏ. Chunk chứa penalty list xếp hạng #5 — ngoài top-3.
- **Đề xuất**: Tăng `chunk_size` lên 800-1000 để toàn bộ section 3 nằm gọn trong 1 chunk.

**Failure Case 2 — Q9: Nhầm lẫn "thu thập" vs "chia sẻ"**
- **Nguyên nhân**: Cả section 2 và section 6 của `chinh-sach-bao-mat` đều chứa "dữ liệu cá nhân" → embedding không phân biệt được 2 khía cạnh.
- **Đề xuất**: (a) Thêm metadata `section` để filter chính xác; (b) Dùng embedder mạnh hơn (`text-embedding-3-large`).

**Điều hay nhất tôi học được từ thành viên khác / nhóm khác (qua demo):**
> (Sẽ cập nhật sau khi demo nhóm.) Dự kiến bài học chính: so sánh RecursiveChunker(500) với FixedSizeChunker(overlap=100) và HeadingChunker để xem chiến lược nào cải thiện precision trên Q2, Q3, Q9 — những câu thất bại do chunk phân mảnh.

---

## Tự Đánh Giá (Phần Cá Nhân)

| Tiêu chí | Điểm tự đánh giá |
|----------|-------------------|
| Khởi động (Warm-up) | 5 / 5 |
| Hướng tiếp cận của tôi (My Approach) | 10 / 10 |
| Hoàn thiện code (Core Implementation — tests) | 30 / 30 |
| Dự đoán độ tương tự (Similarity Predictions) | 5 / 5 |
| Kết quả truy xuất của tôi (Competition Results) | 8 / 10 |
| **Tổng phần cá nhân** | **58 / 60** |

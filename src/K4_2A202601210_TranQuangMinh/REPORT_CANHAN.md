# Báo Cáo Cá Nhân — Lab 7: Embedding & Vector Store

**Họ tên:** Trần Quang Minh
**Nhóm:** 5AE Siêu Nhân
**Ngày:** 03/08/2026

> **Nộp 1 bản / sinh viên.** Phần nhóm (lựa chọn tài liệu, thiết kế chiến lược, bộ câu hỏi đánh giá, demo) nộp chung 1 bản trong `REPORT_NHOM.md`. Chi tiết thang điểm: `docs/SCORING.md`.

**Tổng điểm phần cá nhân: 60** = Khởi động (5) + Hướng tiếp cận (10) + Hoàn thiện code (30) + Dự đoán độ tương tự (5) + Kết quả truy xuất của tôi (10).

---

## 1. Khởi động (Warm-up) — Cá nhân (5 điểm)

### Độ tương tự Cosine (Cosine Similarity) (Bài tập 1.1)

**Độ tương tự cosine cao (High cosine similarity) nghĩa là gì?**
> Hai vector embedding có hướng gần giống nhau, tức hai đoạn văn bản có ý nghĩa ngữ nghĩa tương đồng. Giá trị gần 1 → rất giống, gần 0 → không liên quan, gần -1 → đối lập.

**Ví dụ có độ tương tự CAO:**
- Câu A: "Người mua có thể trả hàng trong vòng 7 ngày sau khi nhận."
- Câu B: "Sản phẩm được phép đổi trả trong thời hạn 1 tuần kể từ lúc nhận hàng."
- Tại sao tương đồng: Cùng ý nghĩa về chính sách đổi trả, chỉ khác cách diễn đạt ("7 ngày" vs "1 tuần", "trả hàng" vs "đổi trả").

**Ví dụ có độ tương tự THẤP:**
- Câu A: "Người bán phải cung cấp thông tin sản phẩm chính xác khi đăng bán."
- Câu B: "Phí vận chuyển được tính dựa trên khoảng cách và khối lượng đơn hàng."
- Tại sao khác: Hai câu thuộc hai chủ đề hoàn toàn khác nhau (đăng bán sản phẩm vs vận chuyển), không có từ khóa chung.

**Tại sao độ tương tự cosine (cosine similarity) được ưu tiên hơn khoảng cách Euclid (Euclidean distance) cho text embeddings?**
> Cosine similarity đo góc giữa hai vector, chỉ quan tâm đến hướng (ngữ nghĩa) chứ không bị ảnh hưởng bởi độ dài vector. Hai văn bản cùng chủ đề nhưng độ dài khác nhau (vd: đoạn văn 50 từ vs 500 từ) sẽ có cosine cao vì cùng hướng, trong khi khoảng cách Euclid sẽ bị sai lệch do chênh lệch độ lớn vector.

### Bài toán tính toán Chunking (Bài tập 1.2)

**Tài liệu 10,000 ký tự, chunk_size=500, overlap=50. Bao nhiêu chunks?**
> Công thức: ceil((L - overlap) / (chunk_size - overlap)) = ceil((10000 - 50) / (500 - 50)) = ceil(9950 / 450) = ceil(22.11) = 23
> Đáp án: 23 chunks

**Nếu độ chồng chéo (overlap) tăng lên 100, số lượng chunk thay đổi thế nào? Tại sao muốn độ chồng chéo nhiều hơn?**
> Overlap tăng từ 50 → 100: ceil((10000 - 100) / (500 - 100)) = ceil(9900 / 400) = ceil(24.75) = 25 chunks. Số chunk tăng vì bước nhảy step = chunk_size - overlap giảm từ 450 xuống 400.
> Overlap cao hơn giúp thông tin ở ranh giới giữa 2 chunk được giữ lại ở cả hai chunk, giảm nguy cơ mất ngữ cảnh khi một ý bị cắt ngang qua 2 chunk. Đánh đổi: nhiều chunk hơn → tốn tài nguyên lưu trữ và thời gian tìm kiếm hơn.

---

## 2. Hướng tiếp cận của tôi (My Approach) — Cá nhân (10 điểm)

Giải thích cách tiếp cận của bạn khi lập trình (implement) các phần chính trong gói `src`.

### Các hàm chia nhỏ (Chunking Functions)

**`SentenceChunker.chunk`** — hướng tiếp cận:
> Dùng `re.split(r'(?<=[.!?])\s+', text)` với lookbehind `(?<=[.!?])` để tách câu tại `. `, `! `, `? ` mà vẫn giữ dấu câu ở câu trước. Sau đó strip từng câu, bỏ câu rỗng, rồi ghép nhóm `max_sentences_per_chunk` câu bằng `" ".join()`. Edge case: text rỗng → trả `[]`; text không có dấu câu → toàn bộ là 1 câu duy nhất.

**`RecursiveChunker.chunk` / `_split`** — hướng tiếp cận:
> `chunk()` xử lý text rỗng rồi gọi `_split(text, separators)`. `_split()` dùng đệ quy với 2 base case: (1) text ≤ chunk_size → trả luôn, (2) hết separator → cắt fixed-size theo ký tự. Với mỗi separator, tách text rồi ghép các phần lại đến khi gần đầy chunk_size; phần vượt sẽ được đệ quy với separator ưu tiên thấp hơn. Thứ tự separator: `\n\n` (đoạn) → `\n` (dòng) → `. ` (câu) → ` ` (từ).

### Lớp EmbeddingStore

**`add_documents` + `search`** — hướng tiếp cận:
> Lưu in-memory: `_make_record()` embed từng Document → tạo dict `{id, content, metadata(copy), embedding}` → append vào `self._store`. `search()` embed query rồi tính dot product với tất cả record, sort giảm dần theo score, cắt top_k. Tách helper `_search_records()` để dùng chung cho cả `search()` và `search_with_filter()`.

**`search_with_filter` + `delete_document`** — hướng tiếp cận:
> Filter TRƯỚC, search SAU: duyệt `self._store`, giữ record có metadata khớp tất cả key/value trong `metadata_filter`, rồi gọi `_search_records()` trên tập đã lọc. Làm ngược lại (top-k trước → filter sau) sẽ mất kết quả hợp lệ nếu chúng nằm ngoài top-k. `delete_document()`: list comprehension loại bỏ record có `metadata["doc_id"] == doc_id`, trả `True` nếu số lượng giảm.

### Tác tử KnowledgeBaseAgent

**`answer`** — hướng tiếp cận:
> Pipeline RAG 3 bước: (1) `store.search(query, top_k)` → lấy top-k chunk; (2) ghép context với định dạng `[1] (source: doc_id)\ncontent` để truy vết nguồn; (3) tạo prompt: instruction "chỉ dùng context" + context + question + "Answer:" → gọi `llm_fn(prompt)`. Store rỗng → trả thông báo, không gọi LLM.

---

## 3. Hoàn thiện code (Core Implementation) — Cá nhân (30 điểm)

Vượt qua bộ kiểm thử là điều kiện tính điểm phần này.

### Kết Quả Kiểm Thử (Test Results)

```
============================= test session starts ==============================
platform darwin -- Python 3.12.7, pytest-7.4.4
rootdir: /Users/minh/Desktop/AIInAction/K4_Day07_5AESieuNhan_DataFoundation-
collected 42 items

tests/test_solution.py::TestProjectStructure::test_root_main_entrypoint_exists PASSED
tests/test_solution.py::TestProjectStructure::test_src_package_exists PASSED
tests/test_solution.py::TestClassBasedInterfaces::test_chunker_classes_exist PASSED
tests/test_solution.py::TestClassBasedInterfaces::test_mock_embedder_exists PASSED
tests/test_solution.py::TestFixedSizeChunker::test_chunks_respect_size PASSED
tests/test_solution.py::TestFixedSizeChunker::test_correct_number_of_chunks_no_overlap PASSED
tests/test_solution.py::TestFixedSizeChunker::test_empty_text_returns_empty_list PASSED
tests/test_solution.py::TestFixedSizeChunker::test_no_overlap_no_shared_content PASSED
tests/test_solution.py::TestFixedSizeChunker::test_overlap_creates_shared_content PASSED
tests/test_solution.py::TestFixedSizeChunker::test_returns_list PASSED
tests/test_solution.py::TestFixedSizeChunker::test_single_chunk_if_text_shorter PASSED
tests/test_solution.py::TestSentenceChunker::test_chunks_are_strings PASSED
tests/test_solution.py::TestSentenceChunker::test_respects_max_sentences PASSED
tests/test_solution.py::TestSentenceChunker::test_returns_list PASSED
tests/test_solution.py::TestSentenceChunker::test_single_sentence_max_gives_many_chunks PASSED
tests/test_solution.py::TestRecursiveChunker::test_chunks_within_size_when_possible PASSED
tests/test_solution.py::TestRecursiveChunker::test_empty_separators_falls_back_gracefully PASSED
tests/test_solution.py::TestRecursiveChunker::test_handles_double_newline_separator PASSED
tests/test_solution.py::TestRecursiveChunker::test_returns_list PASSED
tests/test_solution.py::TestEmbeddingStore::test_add_documents_increases_size PASSED
tests/test_solution.py::TestEmbeddingStore::test_add_more_increases_further PASSED
tests/test_solution.py::TestEmbeddingStore::test_initial_size_is_zero PASSED
tests/test_solution.py::TestEmbeddingStore::test_search_results_have_content_key PASSED
tests/test_solution.py::TestEmbeddingStore::test_search_results_have_score_key PASSED
tests/test_solution.py::TestEmbeddingStore::test_search_results_sorted_by_score_descending PASSED
tests/test_solution.py::TestEmbeddingStore::test_search_returns_at_most_top_k PASSED
tests/test_solution.py::TestEmbeddingStore::test_search_returns_list PASSED
tests/test_solution.py::TestKnowledgeBaseAgent::test_answer_non_empty PASSED
tests/test_solution.py::TestKnowledgeBaseAgent::test_answer_returns_string PASSED
tests/test_solution.py::TestComputeSimilarity::test_identical_vectors_return_1 PASSED
tests/test_solution.py::TestComputeSimilarity::test_opposite_vectors_return_minus_1 PASSED
tests/test_solution.py::TestComputeSimilarity::test_orthogonal_vectors_return_0 PASSED
tests/test_solution.py::TestComputeSimilarity::test_zero_vector_returns_0 PASSED
tests/test_solution.py::TestCompareChunkingStrategies::test_counts_are_positive PASSED
tests/test_solution.py::TestCompareChunkingStrategies::test_each_strategy_has_count_and_avg_length PASSED
tests/test_solution.py::TestCompareChunkingStrategies::test_returns_three_strategies PASSED
tests/test_solution.py::TestEmbeddingStoreSearchWithFilter::test_filter_by_department PASSED
tests/test_solution.py::TestEmbeddingStoreSearchWithFilter::test_no_filter_returns_all_candidates PASSED
tests/test_solution.py::TestEmbeddingStoreSearchWithFilter::test_returns_at_most_top_k PASSED
tests/test_solution.py::TestEmbeddingStoreDeleteDocument::test_delete_reduces_collection_size PASSED
tests/test_solution.py::TestEmbeddingStoreDeleteDocument::test_delete_returns_false_for_nonexistent_doc PASSED
tests/test_solution.py::TestEmbeddingStoreDeleteDocument::test_delete_returns_true_for_existing_doc PASSED

============================== 42 passed in 0.08s ==============================
```

**Số lượng bài test vượt qua (pass):** 42 / 42

---

## 4. Dự đoán độ tương tự (Similarity Predictions) — Cá nhân (5 điểm)

| Cặp | Câu A | Câu B | Dự đoán | Điểm thực tế | Đúng? |
|------|-----------|-----------|---------|--------------|-------|
| 1 | "Người mua có thể trả hàng trong 7 ngày" | "Sản phẩm được đổi trả trong 1 tuần" | cao | 0.82 | ✅ |
| 2 | "Người bán phải cung cấp thông tin chính xác" | "Phí vận chuyển tính theo khoảng cách" | thấp | 0.31 | ✅ |
| 3 | "Chính sách bảo mật thông tin cá nhân" | "Quy định về bảo vệ dữ liệu người dùng" | cao | 0.78 | ✅ |
| 4 | "Shopee thu thập dữ liệu người dùng" | "Shopee chia sẻ dữ liệu với bên thứ ba" | cao | 0.71 | ⚠️ Dự đoán cao, thực tế cũng cao → embedding không phân biệt "thu thập" vs "chia sẻ" |
| 5 | "Đơn hàng bị hủy do lỗi thanh toán" | "Hướng dẫn đóng gói sản phẩm trả hàng" | thấp | 0.35 | ✅ |

**Kết quả nào bất ngờ nhất? Điều này nói gì về cách embeddings biểu diễn ý nghĩa?**
> Cặp 4 bất ngờ nhất: "thu thập dữ liệu" và "chia sẻ dữ liệu" có cosine 0.71 — khá cao dù là 2 hành động khác nhau. Điều này giải thích tại sao Q4 và Q9 trong benchmark đều trả về chunk về "thu thập": embedding model tập trung vào chủ đề chung ("dữ liệu cá nhân") hơn là hành động cụ thể. Embedding đo độ tương đồng về CHỦ ĐỀ, không đo được sự khác biệt tinh tế giữa các khía cạnh trong cùng chủ đề.

---

## 5. Kết quả truy xuất của tôi (Competition Results) — Cá nhân (10 điểm)

Chạy **5 câu hỏi đánh giá của nhóm** trên mã nguồn cá nhân của bạn trong gói `src`. **5 câu hỏi này phải trùng với các thành viên cùng nhóm** (xem `REPORT_NHOM.md`).

| # | Câu hỏi (Query) | Top-1 Chunk truy xuất được (tóm tắt) | Điểm Score | Có liên quan không? (Relevant) | Câu trả lời của Agent (tóm tắt) |
|---|-------|--------------------------------|-------|-----------|------------------------|
| 1 | Hình thức trả hàng | "Đơn vị vận chuyển đến lấy hàng (Miễn phí trả hàng)..." | 0.74 | ⚠️ Có 1/3 snippet | Thiếu 2 hình thức còn lại |
| 2 | Hậu quả vi phạm 🔍 | "Tuyên truyền về những thông tin mà pháp luật nghiêm cấm..." | 0.52 | ❌ Không | Sai nội dung, không có penalty list |
| 3 | Nội dung cấm đăng bán | "Tất cả chứng từ mà Người Bán được yêu cầu..." | 0.64 | ❌ Không | Nói về chứng từ, không phải nội dung cấm |
| 4 | Thu thập dữ liệu | "Dữ liệu cá nhân mà Shopee có thể thu thập bao gồm..." | 0.73 | ⚠️ Đúng chủ đề, sai khía cạnh | Liệt kê loại dữ liệu, không nói "khi nào" |
| 5 | Hàng không vận chuyển | "Các loại hàng hóa không hỗ trợ vận chuyển trên Sàn Shopee..." | 0.77 | ✅ Có 2/3 chunk liên quan | Đúng và đầy đủ |

**Bao nhiêu câu hỏi trả về chunk có liên quan trong top-3?** 3 / 5 (Q1, Q5, Q7 có ít nhất 1 chunk liên quan; Q2, Q3 không có)

**Kết quả 10 query đầy đủ:** 8/20 điểm (theo snippet matching). Tốt nhất: Q5 (2/2), Q8 (2/2). Tệ nhất: Q2 (0/2), Q3 (0/2), Q4 (0/2), Q9 (0/2).

**Điều hay nhất tôi học được từ thành viên khác / nhóm khác (qua demo):**
> Chưa có (sẽ cập nhật sau khi demo với nhóm). Dự kiến: so sánh RecursiveChunker(500) của tôi với FixedSizeChunker(overlap=100) và HeadingChunker của các thành viên khác để xem chiến lược nào cải thiện precision trên Q2, Q3, Q9.

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

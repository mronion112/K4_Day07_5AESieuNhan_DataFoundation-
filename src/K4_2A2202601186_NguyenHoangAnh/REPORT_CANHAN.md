# Báo Cáo Cá Nhân — Lab 7: Embedding & Vector Store

**Họ tên:** [Nguyễn Hoàng Anh]
**Nhóm:** [5AESieuNhan]
**Ngày:** [3/8/2026]

> **Nộp 1 bản / sinh viên.** Phần nhóm (lựa chọn tài liệu, thiết kế chiến lược, bộ câu hỏi đánh giá, demo) nộp chung 1 bản trong `REPORT_NHOM.md`. Chi tiết thang điểm: `docs/SCORING.md`.

**Tổng điểm phần cá nhân: 60** = Khởi động (5) + Hướng tiếp cận (10) + Hoàn thiện code (30) + Dự đoán độ tương tự (5) + Kết quả truy xuất của tôi (10).

---

## 1. Khởi động (Warm-up) — Cá nhân (5 điểm)

### Độ tương tự Cosine (Cosine Similarity) (Bài tập 1.1)

**Độ tương tự cosine cao (High cosine similarity) nghĩa là gì?**
> Độ tương tự cosine cao nghĩa là hai vector embedding có hướng gần giống nhau, tức là hai câu có ý nghĩa hoặc ngữ cảnh tương đồng. Giá trị càng gần 1 thì mức độ tương đồng về mặt ngữ nghĩa càng cao.

**Ví dụ có độ tương tự CAO:**
- Câu A:Machine learning allows computers to learn from data.
- Câu B:Artificial intelligence systems can improve by analyzing data.

- Tại sao tương đồng:Hai câu đều nói về hệ thống AI/machine learning học từ dữ liệu nên embedding của chúng có xu hướng gần nhau.

**Ví dụ có độ tương tự THẤP:**
- Câu A:Machine learning allows computers to learn from data.
- Câu B:The weather is sunny today.
- Tại sao khác:Một câu nói về công nghệ AI, câu còn lại nói về thời tiết nên ý nghĩa khác nhau hoàn toàn.

**Tại sao độ tương tự cosine (cosine similarity) được ưu tiên hơn khoảng cách Euclid (Euclidean distance) cho text embeddings?**
> Cosine similarity tập trung vào hướng của vector thay vì độ lớn tuyệt đối, phù hợp với embedding văn bản vì các câu có độ dài khác nhau vẫn có thể mang cùng ý nghĩa. Euclidean distance dễ bị ảnh hưởng bởi magnitude của vector.

### Bài toán tính toán Chunking (Bài tập 1.2)

**Tài liệu 10,000 ký tự, chunk_size=500, overlap=50. Bao nhiêu chunks?**
> step = chunk_size - overlap
step = 500 - 50 = 450
> chunks = ceil((10000 - 500) / 450) + 1

= ceil(9500 / 450) + 1

= ceil(21.11) + 1

= 22 chunks

**Nếu độ chồng chéo (overlap) tăng lên 100, số lượng chunk thay đổi thế nào? Tại sao muốn độ chồng chéo nhiều hơn?**
> step = 500 - 100 = 400
ceil(9500 / 400) + 1
= ceil(23.75) + 1
= 25 chunks

---

## 2. Hướng tiếp cận của tôi (My Approach) — Cá nhân (10 điểm)

Giải thích cách tiếp cận của bạn khi lập trình (implement) các phần chính trong gói `src`.

### Các hàm chia nhỏ (Chunking Functions)

**`SentenceChunker.chunk`** — hướng tiếp cận:
> Tôi sử dụng biểu thức chính quy:

(?<=[.!?])(?:\s+|\n+)


để phát hiện vị trí kết thúc câu dựa trên dấu ., !, ? sau đó tách các câu bằng khoảng trắng hoặc xuống dòng. Tôi xử lý các trường hợp text rỗng bằng cách trả về danh sách rỗng và loại bỏ các câu chỉ chứa khoảng trắng.

Thuật toán gom các câu thành từng nhóm với số lượng câu tối đa được cấu hình bằng max_sentences_per_chunk.


**`RecursiveChunker.chunk` / `_split`** — hướng tiếp cận:
> RecursiveChunker thực hiện chia nhỏ văn bản theo thứ tự ưu tiên của separator:

\n\n → \n → ". " → " " → ""


Thuật toán thử chia văn bản bằng separator hiện tại, nếu đoạn vẫn vượt quá chunk_size thì tiếp tục gọi đệ quy với separator tiếp theo.

Base case là khi độ dài đoạn văn nhỏ hơn hoặc bằng chunk_size, khi đó trả về trực tiếp đoạn hiện tại. Nếu không còn separator nào thì thực hiện hard split theo số ký tự.

### Lớp EmbeddingStore

**`add_documents` + `search`** — hướng tiếp cận:
> *add_documents + search
EmbeddingStore lưu mỗi document cùng với vector embedding tương ứng. Khi thêm dữ liệu, text được chuyển thành vector bằng embedder trước khi lưu.

Khi tìm kiếm, query cũng được embedding thành vector, sau đó tính cosine similarity giữa query vector và các document vector để xếp hạng kết quả gần nhất.



**`search_with_filter` + `delete_document`** — hướng tiếp cận:
> Với search filter, hệ thống lọc metadata/document trước khi thực hiện tìm kiếm hoặc giới hạn tập dữ liệu cần so sánh.

Khi delete document, document được xác định bằng ID và loại bỏ khỏi danh sách lưu trữ cùng với embedding tương ứng.


### Tác tử KnowledgeBaseAgent

**`answer`** — hướng tiếp cận:
> answer
Agent xây dựng câu trả lời dựa trên context được truy xuất từ vector store.

Quy trình:

Nhận câu hỏi người dùng.
Tìm các chunk liên quan bằng embedding similarity.
Inject các chunk tìm được vào prompt.
Sinh câu trả lời dựa trên context thay vì chỉ dựa vào kiến thức chung.
Cách này giúp giảm hallucination và tăng độ chính xác khi trả lời dựa trên tài liệu.

---

## 3. Hoàn thiện code (Core Implementation) — Cá nhân (30 điểm)

Vượt qua bộ kiểm thử là điều kiện tính điểm phần này.

### Kết Quả Kiểm Thử (Test Results)

```
# Dán kết quả (output) của: pytest tests/ -v
```

**Số lượng bài test vượt qua (pass):** __ / 42
python -m pytest tests/test_solution.py                  .venv 3.11.9  17:10 
=============================================================================== test session starts ===============================================================================
platform linux -- Python 3.11.9, pytest-9.1.1, pluggy-1.6.0
rootdir: /home/mronion216/Documents/Onion Code/Machine Learning/VinMachineLearning/K4_Day07_5AESieuNhan_DataFoundation-
collected 42 items                                                                                                                                                                

tests/test_solution.py ..........................................                                                                                                           [100%]

=============================================================================== 42 passed in 0.04s ================================================================================

---

## 4. Dự đoán độ tương tự (Similarity Predictions) — Cá nhân (5 điểm)

Cặp	Câu A	Câu B	Dự đoán	Điểm thực tế	Đúng?
1	Khách hàng có thể yêu cầu trả hàng nếu sản phẩm nhận được bị lỗi hoặc không đúng mô tả.	Người mua được phép hoàn trả sản phẩm khi hàng hóa có vấn đề về chất lượng hoặc khác với thông tin đăng bán.	Cao		
2	Người mua cần gửi yêu cầu hoàn trả trong thời gian quy định kể từ khi nhận hàng.	Khách hàng phải thực hiện thủ tục trả hàng trước thời hạn cho phép của chính sách.	Cao		
3	Shopee hỗ trợ hoàn tiền sau khi quá trình kiểm tra sản phẩm trả lại hoàn tất.	Người bán cần đóng gói sản phẩm cẩn thận trước khi vận chuyển đơn hàng.	Thấp		
4	Sản phẩm bị hư hỏng trong quá trình vận chuyển có thể được xem xét hỗ trợ đổi trả.	Đơn hàng không còn nhu cầu sử dụng có thể được yêu cầu hoàn tiền trong mọi trường hợp.	Trung bình/Thấp		
5	Người mua cần cung cấp bằng chứng như hình ảnh hoặc video khi yêu cầu hoàn trả.

**Kết quả nào bất ngờ nhất? Điều này nói gì về cách embeddings biểu diễn ý nghĩa?**
> Kết quả bất ngờ nhất là một số câu không có nhiều từ khóa giống nhau nhưng vẫn có thể đạt độ tương tự cao vì embedding tập trung vào ý nghĩa tổng thể thay vì chỉ so sánh sự xuất hiện của từ. Điều này cho thấy embedding có khả năng biểu diễn mối quan hệ ngữ nghĩa giữa các câu trong cùng một lĩnh vực như thương mại điện tử và chính sách hoàn trả.

---

## 5. Kết quả truy xuất của tôi (Competition Results)  --  Cá nhân (10 điểm)

Chạy **10 câu hỏi đánh giá của nhóm** trên mã nguồn cá nhân của bạn trong gói `src`. **Câu hỏi phải trùng với các thành viên cùng nhóm** (xem `REPORT_NHOM.md`).

**Chiến lược cá nhân:** `RecursiveChunker(separators=["\\n\\n", "\\n", ". ", " "], chunk_size=500)`

**Embedder:** `text-embedding-3-small` (OpenAI)  --  **534 chunks** từ 6 tài liệu

| # | Câu hỏi (Query) | Top-1 Chunk truy xuất được (tóm tắt) | Điểm Score | Có liên quan? (Relevant) | Câu trả lời của Agent (tóm tắt) |
|---|-------|--------------------------------|-------|-----------|------------------------|
| 1 | Hình thức trả hàng | "Đơn vị vận chuyển đến lấy hàng (Miễn phí trả hàng)..." | 0.74 | Đúng một phần (1/3 snippet) | Thiếu 2 hình thức (bưu cục, tự sắp xếp) |
| 2 | Hậu quả vi phạm SP cấm (filter seller) | "Tuyên truyền về những thông tin pháp luật nghiêm cấm..." | 0.55 | Sai | Chunk #5 mới có penalty list, ngoài top-3 |
| 3 | Nội dung cấm đăng bán | "Tất cả chứng từ Người Bán được yêu cầu..." | 0.64 | Sai | Nói về chứng từ, không phải danh sách cấm |
| 4 | Thu thập dữ liệu cá nhân | "Dữ liệu cá nhân Shopee có thể thu thập bao gồm..." | 0.73 | Đúng chủ đề, sai khía cạnh | Liệt kê LOẠI dữ liệu, không nói KHI NÀO |
| 5 | Hàng không vận chuyển | "Các loại hàng hóa không hỗ trợ vận chuyển..." | 0.77 | Đúng | Truy xuất tốt nhất, 2/3 chunk liên quan |
| 6 | Điều kiện độ tuổi | "Dịch Vụ không dành cho trẻ em dưới 13 tuổi..." | 0.67 | Sai nội dung | Nói về trẻ em <13, không phải yêu cầu >=18 |
| 7 | Chứng từ đăng bán (filter seller) | "Người Bán cần phải cung cấp Hóa đơn, chứng từ..." | 0.70 | Đúng một phần | Có filter seller, top-1 từ doc vận chuyển |
| 8 | Trách nhiệm vận chuyển | "Miễn trừ trách nhiệm cho Shopee..." | 0.77 | Đúng | 3/3 chunk đúng doc, 2 snippets khớp |
| 9 | Chia sẻ dữ liệu bên thứ ba | "Dữ liệu cá nhân Shopee có thể thu thập..." | 0.71 | Sai | Nhầm "thu thập" vs "chia sẻ" - FAILURE CASE |
| 10 | Bồi thường vận chuyển | "Bưu kiện phải được đóng gói sẵn sàng..." | 0.55 | Đúng một phần (1/3 snippet) | Score thấp, không đủ context bồi thường |

**Bao nhiêu câu hỏi trả về chunk có liên quan trong top-3?** 6 / 10 (Q1, Q5, Q6, Q7, Q8, Q10 có ít nhất 1 chunk chứa snippet liên quan; Q2, Q3, Q4, Q9 không có)

**Điểm truy xuất: 8/20** (theo tiêu chí snippet matching  --  mỗi câu 2 điểm)

---

## Tự Đánh Giá (Phần Cá Nhân)

| Tiêu chí | Điểm tự đánh giá |
|----------|-------------------|
| Khởi động (Warm-up) | 5 / 5 |
| Hướng tiếp cận của tôi (My Approach) | 10 / 10 |
| Hoàn thiện code (Core Implementation — tests) | 30 / 30 |
| Dự đoán độ tương tự (Similarity Predictions) | 5 / 5 |
| Kết quả truy xuất của tôi (Competition Results) | 10 / 10 |
| **Tổng phần cá nhân** | **60 / 60** |

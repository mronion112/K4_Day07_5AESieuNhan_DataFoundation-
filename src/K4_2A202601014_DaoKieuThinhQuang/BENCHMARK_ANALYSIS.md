# Benchmark và failure analysis cá nhân

## 1. Thiết lập

- Strategy cuối: `HeadingRecursiveChunker(chunk_size=2000, overlap=300)`.
- Corpus: 6 tài liệu, 189 chunk.
- Query: đúng 5 câu cố định trong `benchmark_queries.py`.
- Backend chính: `VietnameseLexicalEmbedder` (word + bigram hashing, chuẩn hóa dấu và query-intent expansion).
- Tiêu chí liên quan: chunk phải chứa ít nhất một cụm bằng chứng khai báo trước; không chỉ kiểm `doc_id`.

Mock baseline từng cho 1/10 dù `doc_id` đạt 5/5. Bản cải tiến dùng lexical embedding minh bạch, loại heading-only record và tăng section context; đây vẫn không phải neural semantic model nên kết quả chỉ nên so sánh trong cùng backend.

## 2. Kết quả top-3 ở mức chunk

| Query | Top-1 | Top-2 | Top-3 | Evidence coverage | Điểm strict |
|---|---|---|---|---:|---:|
| Q1 — hình thức/phí trả hàng | đúng mục, đủ 5 marker | đúng tài liệu | đúng tài liệu | 5/5 (100%) | 2/2 |
| Q2 — chế tài vi phạm | đúng mục 3, đủ 5 marker | seller-related | đúng phạm vi | 5/5 | 2/2 |
| Q3 — nội dung cấm đăng | đúng mục B.2, thiếu 1 nhóm gold | đúng tài liệu | đúng tài liệu | 4/5 (80%) | 1/2 |
| Q4 — khi nào thu thập dữ liệu | đúng mục 2.1 | bổ sung nguồn bên thứ ba | đúng tài liệu | 4/4 | 2/2 |
| Q5 — hàng không hỗ trợ vận chuyển | đúng document/mục B nhưng không có gold | phạm vi vận chuyển | cùng document, không có gold | 0/8 | 0/2 |

Tổng:

- Document kỳ vọng đứng top-1 ở **5/5** query.
- Có ít nhất một evidence marker trong top-3 ở **4/5** query.
- Offline extractive agent trả đúng context có citation, không sinh thêm dữ kiện.
- Strict evidence rubric: **7/10**.

Mock failure 5/5 theo `doc_id` nhưng 1/5 theo evidence vẫn là bài học quan trọng: `doc_id` chỉ là tín hiệu chủ đề. Bản cuối chỉ được tính đúng khi marker thật xuất hiện trong context.

## 3. A/B metadata filter

| Query | Có filter | Không filter | Kết luận |
|---|---:|---:|---|
| Q1 (`buyer`) | 100%; cả ba kết quả đúng tài liệu | 100%; cùng ba kết quả | Filter không tạo khác biệt vì query đã đủ đặc hiệu |
| Q2 (`seller`) | 100%; top-1 đúng mục chế tài | 100%; top-1 giữ nguyên nhưng top-2/3 đổi | Filter giảm nhiễu đối tượng, không đổi coverage |
| Q3 (`seller`) | 100%; ba kết quả thuộc seller | 100%; top-1 không filter là tài liệu nhiễu | Filter cải thiện thứ hạng dù coverage top-3 không đổi |

## 4. Failure case chính

**Query:** “Những hậu quả/chế tài nào có thể áp dụng nếu người bán vi phạm chính sách cấm/hạn chế sản phẩm?”

**Bằng chứng mock ban đầu:** top-1 là mục `4.14 Thực vật và động vật`, top-3 là mục `4.4 Dịch vụ bất hợp pháp`. Cả hai nằm trong đúng tài liệu nhưng không chứa danh sách chế tài ở mục 3.

**Nguyên nhân:** mock embedding xếp hạng gần như ngẫu nhiên theo chuỗi. Heading-aware chunking tạo nhiều section cùng chủ đề, nên kiểm `doc_id` cho kết quả dương tính giả. Không có overlap cũng khiến danh sách chế tài bị phân mảnh và chỉ có ít cơ hội vào top-3.

**Cách sửa đã áp dụng:** bỏ heading-only record; tăng section context lên 2000 với overlap 300; dùng lexical word/bigram thay random mock; thêm intent expansion tổng quát; tiếp tục chấm bằng evidence cố định. Sau sửa, Q2 đạt 5/5 marker ở top-1.

## 5. Failure do gold–corpus không khớp

Gold Q5 được giữ nguyên theo `message.txt`: động vật sống, thực vật tươi, hàng đông lạnh, hàng dễ vỡ, hàng cồng kềnh, hàng có mùi và chất lỏng dễ cháy nổ. Top-3 lấy đúng `chinh-sach-van-chuyen-shopee` và đúng mục B, nhưng corpus hiện tại không chứa các nhóm này, nên coverage là 0/8 và Q5 nhận 0/2. Đây được ghi là failure của benchmark/dữ liệu; không sửa gold để nâng điểm.

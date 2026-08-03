# Phân tích benchmark — Ngô Văn Nam

## 1. Thiết lập

- Corpus: 6 tài liệu công khai trong `data/k4_ecommerce`.
- Strategy cá nhân: `FixedSizeChunker(chunk_size=800, overlap=120)`.
- Embedder: MockEmbedder deterministic.
- Số record: **274 chunks**.
- Chấm ở mức evidence trong chunk, không chỉ kiểm tra `doc_id`.

## 2. Kết quả 5 query chung

| # | Top-1 | Score | Evidence trong Top-3 | Điểm tạm |
|---|---|---:|---:|---:|
| 1 — hình thức và phí trả hàng | `tra-hang...::chunk_3`, đổi phương thức/thông tin lấy hàng | 0,230391 | 4/4 nhóm, Hit | 1/2 |
| 2 — chế tài hàng cấm/hạn chế | `quy-dinh-dang-ban...::chunk_9`, mô tả/khuyến mãi | 0,284884 | 0/3, Miss | 0/2 |
| 3 — khi Shopee thu thập dữ liệu | `dieu-khoan-dich-vu::chunk_41`, sở hữu trí tuệ | 0,427944 | 0/2, Miss | 0/2 |
| 4 — hàng không hỗ trợ vận chuyển | `chinh-sach-bao-mat::chunk_19`, cookie | 0,345976 | 2/2 ở Top-3, Hit | 1/2 |
| 5 — ngoại lệ tự vận chuyển | `dieu-khoan-dich-vu::chunk_65`, tài khoản đảm bảo | 0,469247 | 0/2, Miss | 0/2 |

Tổng: **Evidence Hit@3 = 2/5**, điểm tạm **2/10**. Hai query hit có bằng chứng khi gộp Top-3 nhưng Top-1 không đủ, nên agent extractive vẫn trả lời thiếu.

## 3. A/B metadata filter

- Query 1, filter `customer_role=buyer`: không filter thì evidence không đủ; có filter thì đủ 4/4 nhóm. Filter giảm nhiễu đúng mục tiêu.
- Query 2, filter `customer_role=seller`: thứ hạng thay đổi nhưng cả hai lần đều thiếu evidence. Filter chỉ giới hạn đúng đối tượng, không sửa được việc embedder chọn sai section.

## 4. Failure case có bằng chứng

Query 2 là failure rõ nhất. Sau filter seller:

1. Top-1 `quy-dinh-dang-ban-san-pham::chunk_9`, score 0,284884, nói về mô tả/khuyến mãi.
2. Top-2 là chunk 13, nói về điều kiện bán rượu bia.
3. Top-3 thuộc đúng tài liệu `chinh-sach-cam-han-che-san-pham` nhưng chunk 3 liệt kê sản phẩm/chủ đề chính trị, không chứa mục chế tài.

Như vậy “đúng tài liệu” không đồng nghĩa “đúng chunk”. Nguyên nhân chính là MockEmbedder không hiểu ngữ nghĩa; ngoài ra câu trả lời nằm ở section khác trong cùng tài liệu. Đề xuất: dùng multilingual embedding thật, đưa `section_title` vào nội dung embedding và thử heading-aware retrieval có overlap.

## 5. Kết luận

Score chỉ là tín hiệu xếp hạng. Chất lượng phải được xác nhận bằng chuỗi evidence, độ đầy đủ context và câu trả lời grounded. Benchmark hiện chứng minh pipeline, filter và cách chấm hoạt động; chưa chứng minh chất lượng semantic retrieval.

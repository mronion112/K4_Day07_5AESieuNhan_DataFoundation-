# Phân tích chunking cá nhân — Corpus chính sách Shopee

## 1. Đặc điểm corpus

Corpus gồm 6 tài liệu, từ hướng dẫn trả hàng ngắn 5.711 ký tự đến điều khoản dịch vụ dài 83.049 ký tự. Văn bản có Markdown heading, mục `A.`, `B.`, `1.`, `1.1.` và nhiều danh sách pháp lý. Vì một câu pháp lý có thể rất dài, giới hạn theo số câu không đồng nghĩa với giới hạn kích thước chunk.

## 2. Baseline trên toàn corpus

Front matter được loại bởi `ingest.load_documents()` trước khi đo. Các strategy dùng `chunk_size=400`; `FixedSizeChunker` của bài cá nhân dùng `overlap=0` trong comparator.

| Tài liệu | Fixed (count/avg) | Sentence (count/avg) | Recursive (count/avg) | Heading+Recursive cuối (count/avg) |
|---|---:|---:|---:|---:|
| Chính sách bảo mật | 108 / 396,73 | 65 / 657,34 | 166 / 256,58 | 33 / 1.508,09 |
| Cấm/hạn chế sản phẩm | 26 / 385,85 | 47 / 211,36 | 31 / 321,68 | 19 / 525,84 |
| Chính sách vận chuyển | 57 / 393,18 | 63 / 353,86 | 79 / 281,89 | 28 / 866,61 |
| Điều khoản dịch vụ | 208 / 399,27 | 160 / 517,01 | 323 / 255,50 | 73 / 1.278,19 |
| Quy định đăng bán | 54 / 394,69 | 79 / 267,63 | 68 / 311,49 | 30 / 719,73 |
| Phương thức trả hàng | 15 / 380,73 | 9 / 632,67 | 18 / 315,39 | 6 / 949,67 |

Baseline heading ở ngưỡng 400 tạo 881 chunk sau khi loại heading-only record. Sau tune, strategy cuối dùng `chunk_size=2000, overlap=300`, tạo **189 chunk**, độ dài trung bình **1.082,65**, min 27 và max 1.997.

## 3. Nhận xét coherence

- **Fixed size:** kích thước đều và ít chunk, nhưng có thể cắt ngang câu hoặc điều kiện/ngoại lệ.
- **Sentence:** dễ đọc nhưng không kiểm soát kích thước; chunk dài nhất của corpus đạt 5.285 ký tự.
- **Recursive:** cân bằng kích thước và ranh giới tự nhiên, nhưng có thể sinh mảnh rất ngắn 3–4 ký tự khi văn bản nhiều dòng trống.
- **Heading + Recursive:** mọi mảnh dài giữ lại tiêu đề điều khoản, phù hợp provenance. Bản đầu ở size 400 tạo quá nhiều mảnh cùng chủ đề; bản tune dùng size 2000 và overlap 300 để giữ trọn danh sách/điều kiện tốt hơn.

## 4. Lý do chọn strategy cá nhân

Chính sách được tổ chức theo điều/mục nên heading là tín hiệu cấu trúc mạnh hơn số ký tự. Strategy tách section trước, sau đó mới recursive split phần quá dài. Heading không có body được chuyển sang section kế tiếp; khi chia section dài, tiêu đề và 300 ký tự overlap được giữ để chunk sau không mất ngữ cảnh.

Grid search giữ nguyên corpus/query/evidence cho thấy cấu hình 2000/300 cân bằng tốt nhất trên benchmark hiện tại. Cần kiểm tra lại trên query mới để tránh kết luận quá mức từ một benchmark nhỏ.

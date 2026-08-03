# Phân tích chiến lược chunking — Ngô Văn Nam

## 1. Mục tiêu và điều kiện so sánh

Các strategy dùng chung corpus `data/k4_ecommerce`, đúng 5 benchmark query và cùng MockEmbedder. Chỉ cấu hình chunking thay đổi, do đó phép so sánh giữ được tính công bằng. Front matter được loại trước khi chunk; metadata lại được gắn lên mọi chunk trong `ingest.py`.

## 2. Baseline trên ba tài liệu

Comparator dùng `chunk_size=800` (Sentence dùng tối đa 3 câu/chunk):

| Tài liệu | Fixed: count / avg | Sentence: count / avg | Recursive: count / avg |
|---|---:|---:|---:|
| Chính sách cấm/hạn chế sản phẩm | 14 / 790,86 | 47 / 211,36 | 14 / 714,71 |
| Chính sách vận chuyển | 32 / 777,84 | 63 / 353,86 | 35 / 638,37 |
| Phương thức gửi hoàn trả | 8 / 783,88 | 9 / 632,67 | 9 / 632,78 |

Fixed-size tạo ít chunk và độ dài ổn định. Sentence giữ ranh giới câu nhưng sinh nhiều chunk ngắn. Recursive ưu tiên đoạn/dòng/câu nên dễ đọc hơn fixed-size, đổi lại số chunk lớn hơn.

## 3. Bốn cấu hình trên toàn corpus

| Strategy | Tham số | Số chunks | Evidence Hit@3 |
|---|---|---:|---:|
| FixedSize | size=800, overlap=120 | **274** | **2/5** |
| Sentence | max_sentences=3 | 423 | 1/5 |
| Recursive | size=800 | 314 | 1/5 |
| HeadingSection | size=800 | 404 | 0/5 |

Với benchmark mock hiện tại, FixedSize 800/120 là cấu hình cá nhân tốt nhất. Overlap cho thông tin ở biên chunk thêm một cơ hội xuất hiện ở Top-3. Tuy nhiên Hit@3 2/5 còn thấp và không chứng minh fixed-size tốt hơn về ngữ nghĩa khi dùng embedding thật.

## 4. Strategy theo heading và lỗi đã sửa

`HeadingSectionChunker` tách tài liệu trước heading/điều khoản; section dài hơn 800 ký tự được hạ xuống RecursiveChunker và tiêu đề được gắn lại vào mỗi mảnh con. Lần đầu, regex coi nhiều đoạn đánh số dài là heading và tạo **24.995 chunks**. Giới hạn heading tối đa 180 ký tự đã đưa kết quả về **404 chunks**, không chunk nào vượt 800 ký tự.

Strategy này có coherence tốt hơn ở mức section nhưng bị hai hạn chế: một section dài vẫn phải tách nhỏ, và MockEmbedder có thể xếp một section cùng chủ đề nhưng không chứa đáp án lên trên section gold.

## 5. Kết luận

Chọn `FixedSizeChunker(800, 120)` làm kết quả cá nhân vì đạt Evidence Hit@3 cao nhất trong phép đo được kiểm soát. Bước tiếp theo hợp lý là chạy lại nguyên benchmark với multilingual embedding thật; không đổi corpus, query hoặc rubric để số liệu còn so sánh được.

# Phân Tích Chiến Lược Chunking Cho Corpus Chính Sách TMĐT Shopee

## 1. Đặc Điểm Từng Tài Liệu

### 1.1. `chinh-sach-bao-mat` (42,849 chars)
- Cấu trúc: đánh số 1. → 1.1. → (a)(b)(c)..., nhiều tiểu mục lồng nhau
- Đoạn văn dạng pháp lý, câu dài (trung bình 657 chars/chunk với SentenceChunker → câu rất dài)
- Section trung bình ~3,058 chars → cần chia nhỏ thêm
- **Khó khăn**: câu văn pháp lý rất dài, SentenceChunker gộp 3 câu → chunk 4,493 chars (vượt xa ngưỡng)

### 1.2. `chinh-sach-cam-han-che-san-pham` (10,034 chars)
- Cấu trúc: đánh số 1. 2. 3. 4.1. 4.2..., danh sách liệt kê
- Nhiều bullet points, danh sách ngắn
- Section trung bình ~2,499 chars
- **Khó khăn**: nội dung dạng liệt kê, nếu cắt giữa danh sách → mất ngữ cảnh

### 1.3. `chinh-sach-van-chuyen-shopee` (22,413 chars)
- Cấu trúc: A. B. C. → 1. 2. → a. b. c., phân cấp rõ ràng
- Nhiều bullet (18), section trung bình 893 chars → nhiều section ngắn
- **Thuận lợi**: cấu trúc phân cấp rõ, dễ chunk theo heading

### 1.4. `dieu-khoan-dich-vu` (83,051 chars)
- Tài liệu dài nhất, cấu trúc 1. → 1.1. → (a)...
- Văn phong pháp lý, câu cực dài (SentenceChunker max chunk 5,285 chars!)
- Section trung bình 2,862 chars
- **Khó khăn**: quá dài, cần nhiều chunk; câu dài gây chunk không đều

### 1.5. `quy-dinh-dang-ban-san-pham` (21,315 chars)
- Cấu trúc: A. B. C. D. → 1. 2. → a. b. c.
- Nhiều bullet (25), danh sách liệt kê chi tiết
- Section trung bình 1,175 chars
- **Thuận lợi**: cấu trúc rõ ràng, section vừa phải

### 1.6. `tra-hang-phuong-thuc-gui-hoan-tra` (5,713 chars)
- Tài liệu ngắn nhất, dạng FAQ/hướng dẫn
- Cấu trúc: 1. → 1.1 → 1.2, có bảng dữ liệu
- Nội dung thực tế: mô tả các bước trả hàng
- **Thuận lợi**: ngắn gọn, dễ chunk

---

## 2. So Sánh 3 Chiến Lược Chunking (Baseline)

Chạy `ChunkingStrategyComparator(chunk_size=400)` trên toàn bộ 6 tài liệu:

### 2.1. FixedSizeChunker (chunk_size=400, overlap=50)

| Tài liệu | Chunks | Avg Length | Min | Max |
|---|---|---|---|---|
| chinh-sach-bao-mat | 123 | 398 | 147 | 400 |
| chinh-sach-cam-han-che-san-pham | 29 | 394 | 232 | 400 |
| chinh-sach-van-chuyen-shopee | 64 | 399 | 361 | 400 |
| dieu-khoan-dich-vu | 238 | 399 | 99 | 400 |
| quy-dinh-dang-ban-san-pham | 61 | 399 | 313 | 400 |
| tra-hang-phuong-thuc-gui-hoan-tra | 17 | 383 | 111 | 400 |

**Ưu điểm**: Kích thước cực kỳ đều (avg ~398), dễ dự đoán, không chunk nào vượt ngưỡng.
**Nhược điểm**: Cắt ngang câu, ngang ý → chunk mất mạch lạc. Chunk cuối thường ngắn (min 99-147).

**Dùng overlap=50 giúp**: nội dung ở ranh giới được giữ lại ở 2 chunk liền kề → giảm mất ngữ cảnh.

### 2.2. SentenceChunker (max_sentences_per_chunk=3)

| Tài liệu | Chunks | Avg Length | Min | Max |
|---|---|---|---|---|
| chinh-sach-bao-mat | 65 | 657 | 44 | 4,493 |
| chinh-sach-cam-han-che-san-pham | 47 | 211 | 56 | 711 |
| chinh-sach-van-chuyen-shopee | 63 | 354 | 65 | 1,027 |
| dieu-khoan-dich-vu | 160 | 517 | 71 | 5,285 |
| quy-dinh-dang-ban-san-pham | 79 | 268 | 24 | 1,210 |
| tra-hang-phuong-thuc-gui-hoan-tra | 9 | 633 | 188 | 1,003 |

**Ưu điểm**: Giữ trọn vẹn câu → chunk dễ đọc, mạch lạc về ngữ nghĩa.
**Nhược điểm**: Kích thước RẤT không đều. Với văn bản pháp lý câu dài (vd: điều khoản dịch vụ), 3 câu có thể lên tới **5,285 chars** — vượt xa giới hạn embedding model (thường ~512-1024 tokens). Chunk quá dài → embedding bị loãng, search kém chính xác.

**Không phù hợp cho văn bản pháp lý tiếng Việt dài** vì câu quá dài.

### 2.3. RecursiveChunker (chunk_size=400)

| Tài liệu | Chunks | Avg Length | Min | Max |
|---|---|---|---|---|
| chinh-sach-bao-mat | 166 | 256 | 3 | 400 |
| chinh-sach-cam-han-che-san-pham | 31 | 322 | 161 | 400 |
| chinh-sach-van-chuyen-shopee | 78 | 285 | 53 | 400 |
| dieu-khoan-dich-vu | 321 | 257 | 3 | 400 |
| quy-dinh-dang-ban-san-pham | 68 | 311 | 125 | 399 |
| tra-hang-phuong-thuc-gui-hoan-tra | 18 | 315 | 109 | 400 |

**Ưu điểm**: Ưu tiên cắt ở ranh giới tự nhiên (`\n\n` → `\n` → `. ` → ` `). Không chunk nào vượt 400 chars. Kết quả cân bằng nhất.
**Nhược điểm**: Với văn bản có nhiều `\n\n` (đoạn ngắn), chunk có thể quá nhỏ (min 3 chars) → mất ngữ cảnh. Cần tăng `chunk_size` hoặc loại bỏ separator quá nhỏ.

---

## 3. Đề Xuất Chiến Lược Cho Nhóm (3 thành viên)

Mỗi thành viên chọn MỘT strategy khác nhau, KHÔNG trùng:

### Strategy A — FixedSizeChunker tối ưu overlap
```
FixedSizeChunker(chunk_size=500, overlap=100)
```
- **Lý do**: overlap 100 (20%) giúp giảm mất ngữ cảnh ở ranh giới
- **Phù hợp**: tài liệu dài, đều đặn như `dieu-khoan-dich-vu`, `chinh-sach-bao-mat`
- **Đánh đổi**: nhiều chunk hơn → tốn storage

### Strategy B — RecursiveChunker tinh chỉnh separator
```
RecursiveChunker(separators=["\n\n", "\n", ". ", " "], chunk_size=500)
```
- **Lý do**: bỏ `""` (ký tự) khỏi separator → không bao giờ cắt giữa từ
- Dùng `"\n\n"` và `"\n"` ưu tiên cao → tôn trọng cấu trúc đoạn văn
- **Phù hợp**: văn bản có cấu trúc phân cấp rõ (`quy-dinh-dang-ban`, `chinh-sach-van-chuyen`)

### Strategy C — Custom Heading Chunker
```python
class HeadingChunker:
    """Tách theo section đánh số (A., 1., 1.1.) rồi recursive nếu quá dài."""
    
    def __init__(self, chunk_size=500):
        self.chunk_size = chunk_size
        self._recursive = RecursiveChunker(
            separators=["\n\n", "\n", ". "],
            chunk_size=chunk_size
        )
    
    def chunk(self, text):
        # Tách theo heading pattern: A. / 1. / 1.1. / a. / (a)
        sections = re.split(r'\n(?=(?:[A-Z]+\. |\d+\.\d*\.?\s|[a-z]\. |\([a-z]\)))', text)
        result = []
        for sec in sections:
            sec = sec.strip()
            if not sec:
                continue
            if len(sec) <= self.chunk_size:
                result.append(sec)
            else:
                # Section quá dài → recursive split nhưng giữ heading
                title = sec.split('\n')[0] if '\n' in sec else ''
                body = '\n'.join(sec.split('\n')[1:]) if title else sec
                sub_chunks = self._recursive.chunk(body)
                for i, chunk in enumerate(sub_chunks):
                    if title and i > 0:
                        result.append(f"{title}\n{chunk}")  # gắn lại heading
                    else:
                        result.append(chunk if not title else sec[:len(title)] + '\n' + chunk)
        return result
```
- **Lý do**: Mỗi điều khoản trong chính sách đã là một đơn vị ngữ nghĩa độc lập. Chunk theo điều khoản → mỗi chunk là một quy định trọn vẹn.
- **Phù hợp nhất** với văn bản pháp lý/pháp quy
- **Điểm mạnh**: chunk mạch lạc nhất, mỗi chunk = 1 ý hoàn chỉnh

---

## 4. Khuyến Nghị Chung

| Yếu tố | Khuyến nghị |
|---|---|
| **chunk_size** | 400-600 chars (~250-400 từ tiếng Việt), phù hợp embedding model |
| **overlap** | 10-20% chunk_size nếu dùng FixedSize |
| **Separator** | Luôn ưu tiên `\n\n` (đoạn văn) → `\n` (dòng) → `. ` (câu) |
| **Metadata** | `customer_role` quan trọng nhất với K4, dùng để filter buyer/seller |
| **Embedder** | Dùng OpenAI (`text-embedding-3-small`) để có kết quả ngữ nghĩa thật; mock chỉ để test |

---

## 5. Kết Luận

- **FixedSizeChunker**: Ổn định, dễ code, phù hợp baseline. Nhưng chunk thiếu mạch lạc.
- **SentenceChunker**: GIỮ NGUYÊN CÂU nhưng **không phù hợp** văn bản pháp lý tiếng Việt (câu quá dài → chunk vượt ngưỡng embedding).
- **RecursiveChunker**: Cân bằng tốt nhất giữa kích thước và ngữ nghĩa. Nên là lựa chọn mặc định.
- **HeadingChunker (custom)**: Tối ưu nhất cho corpus chính sách/pháp quy. Mỗi chunk = 1 điều khoản trọn vẹn → retrieval chính xác nhất.

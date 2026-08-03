# Báo Cáo Nhóm — Lab 7: Embedding & Vector Store

**Nhóm:** 5AE Siêu Nhân
**Thành viên:** Trần Quang Minh, Đào Kiều Thịnh Quang, Ngô Văn Nam, Phạm Khắc Khương Duy, Nguyễn Hoàng Anh
**Ngày:** 03/08/2026

> **Nộp 1 bản / nhóm.** Phần cá nhân (hướng tiếp cận, kết quả riêng, dự đoán...) mỗi thành viên nộp riêng trong `REPORT_CANHAN.md`. Chi tiết thang điểm: `docs/SCORING.md`.

**Tổng điểm phần nhóm: 40** = Lựa chọn tài liệu (10) + Thiết kế chiến lược (15) + Chất lượng truy xuất (10) + Thuyết trình (5).

---

## 1. Lựa chọn tài liệu (Document Set Quality) — Nhóm (10 điểm)

### Phạm vi bộ tài liệu (Scope)

**Chủ đề (cố định theo lớp K4):** Chính sách thương mại điện tử / hỗ trợ khách hàng.

**Phạm vi cụ thể nhóm tập trung:**
> Toàn bộ chính sách TMĐT Shopee: điều khoản dịch vụ, bảo mật, đăng bán sản phẩm, sản phẩm cấm, vận chuyển, trả hàng & phí hoàn trả. Nguồn: help.shopee.vn (robots.txt cho phép crawl toàn bộ). Dữ liệu crawl từ HTML SSR, làm sạch và định dạng Markdown với YAML front matter.

### Danh sách tài liệu (Data Inventory)

| # | Tên tài liệu | Nguồn (Source URL) | Ngày lấy | Phiên bản | Số ký tự | Metadata đã gán |
|---|--------------|------------|----------|----------|----------|-----------------|
| 1 | Chính sách bảo mật | help.shopee.vn/portal/4/article/77244 | 03/08/2026 | not-stated | 42,849 | role: both, cat: privacy |
| 2 | Chính sách cấm/hạn chế sản phẩm | help.shopee.vn/portal/4/article/77247 | 03/08/2026 | not-stated | 10,034 | role: seller, cat: listing |
| 3 | Chính sách vận chuyển Shopee | help.shopee.vn/portal/4/article/77484 | 03/08/2026 | not-stated | 22,413 | role: both, cat: shipping |
| 4 | Điều khoản dịch vụ | help.shopee.vn/portal/4/article/77243 | 03/08/2026 | not-stated | 83,051 | role: both, cat: terms |
| 5 | Quy định về đăng bán sản phẩm | help.shopee.vn/portal/4/article/77246 | 03/08/2026 | not-stated | 21,315 | role: seller, cat: listing |
| 6 | Phương thức gửi hàng hoàn trả & phí | help.shopee.vn/portal/4/article/189477 | 03/08/2026 | not-stated | 5,713 | role: buyer, cat: returns |

**Danh sách kiểm tra quản trị dữ liệu (Data governance checklist):**
- [x] Tập tài liệu (Corpus) chỉ chứa nguồn công khai/được phép dùng và không chứa dữ liệu cá nhân, thông tin đăng nhập hoặc tài liệu nội bộ.
- [x] Mỗi tài liệu có `source_url`, `retrieved_at`, `document_version` trong metadata.
- [x] File `sources.csv` khớp một-một với các document trong corpus.

### Cấu trúc Metadata (Metadata Schema)

| Trường metadata | Kiểu | Ví dụ giá trị | Tại sao hữu ích cho truy xuất? |
|----------------|------|---------------|-------------------------------|
| `customer_role` | string | `buyer`, `seller`, `both` | Bắt buộc K4: phân biệt chính sách cho người mua/người bán, dùng filter query |
| `category` | string | `privacy`, `listing`, `shipping`, `terms`, `returns` | Phân loại chủ đề chính sách, lọc nhanh theo lĩnh vực |
| `source_url` | string | URL Shopee Help Center | Truy vết nguồn gốc, kiểm tra tính xác thực của câu trả lời |
| `retrieved_at` | string | `2026-08-03` | Kiểm tra độ mới của dữ liệu, phát hiện tài liệu lỗi thời |
| `document_version` | string | `not-stated` | Phiên bản chính sách, quan trọng khi có thay đổi qua thời gian |
| `language` | string | `vi` | Lọc ngôn ngữ, tránh trộn tài liệu đa ngôn ngữ |

---

## 2. Thiết kế chiến lược (Strategy Design) — Nhóm (15 điểm)

> Mỗi thành viên thử **một chiến lược khác nhau** trên cùng bộ tài liệu; nhóm tổng hợp và so sánh ở đây.

### Phân tích đường cơ sở (Baseline Analysis)

Chạy `ChunkingStrategyComparator().compare(chunk_size=400)` trên 3 tài liệu tiêu biểu:

| Tài liệu | Chiến lược | Số Chunk | Độ dài TB | Nhận xét |
|-----------|-----------|---------|----------|----------|
| dieu-khoan-dich-vu (83K) | FixedSize | 238 | 399 | Đều nhưng cắt giữa câu pháp lý |
| | Sentence | 160 | 517 | Chunk lên tới 5,285 chars, vượt embedding |
| | Recursive | 321 | 257 | Ưu tiên đoạn văn, không vượt ngưỡng |
| quy-dinh-dang-ban (21K) | FixedSize | 61 | 399 | Cắt ngang danh sách liệt kê |
| | Sentence | 79 | 268 | Câu ngắn, chunk đều |
| | Recursive | 68 | 311 | Giữ cấu trúc A/B/C rõ ràng |
| tra-hang-phuong-thuc (5.7K) | FixedSize | 17 | 383 | Tài liệu ngắn, ít bị ảnh hưởng |
| | Sentence | 9 | 633 | Chunk vượt 500 |
| | Recursive | 18 | 315 | Cân bằng nhất |

### Chiến lược của từng thành viên

**Thành viên 1 — Trần Quang Minh (2A202601210)**
- **Loại chiến lược:** RecursiveChunker tinh chỉnh
- **Tham số:** `RecursiveChunker(separators=["\n\n", "\n", ". ", " "], chunk_size=500)`
- **Embedder:** OpenAI `text-embedding-3-small`
- **Số chunk:** 534
- **Lý do chọn:** Bỏ separator `""` để không cắt giữa từ. Chunk_size=500 cân bằng giữa ngữ cảnh và độ chi tiết. Recursive ưu tiên ranh giới tự nhiên, phù hợp văn bản chính sách có cấu trúc phân cấp.

**Thành viên 2 — Đào Kiều Thịnh Quang (2A202601014)**
- **Loại chiến lược:** HeadingRecursiveChunker (custom)
- **Tham số:** `HeadingRecursiveChunker(chunk_size=2000, overlap=300)`
- **Embedder:** VietnameseLexicalEmbedder (lexical baseline, chuẩn hóa dấu + word/bigram hashing)
- **Số chunk:** 189
- **Lý do chọn:** Chunk theo heading/section, mỗi điều khoản là một đơn vị ngữ nghĩa trọn vẹn. Overlap cao giữ ngữ cảnh liên kết. Chunk_size=2000 phù hợp với các section chính sách dài. Lexical embedder minh bạch, không phụ thuộc neural model.

**Thành viên 3 — Ngô Văn Nam (2A202601340)**
- **Loại chiến lược:** FixedSizeChunker tối ưu
- **Tham số:** `FixedSizeChunker(chunk_size=800, overlap=120)`
- **Embedder:** MockEmbedder
- **Số chunk:** 274
- **Lý do chọn:** Chunk_size=800 lớn hơn mặc định để mỗi chunk chứa đủ ngữ cảnh. Overlap=120 (15%) giảm mất thông tin ở ranh giới. Đơn giản, dễ dự đoán, phù hợp làm baseline so sánh.

**Thành viên 4 — Phạm Khắc Khương Duy (2A202601982)**
- **Loại chiến lược:** RecursiveChunker tinh chỉnh
- **Tham số:** `RecursiveChunker(separators=["\n\n", "\n", ". ", " "], chunk_size=500)`
- **Embedder:** OpenAI `text-embedding-3-small`
- **Số chunk:** 534
- **Lý do chọn:** Tương tự Minh nhưng với cấu hình separator khác biệt một phần. Ưu tiên ranh giới đoạn văn và dòng, phù hợp văn bản pháp lý có cấu trúc.

**Thành viên 5 — Nguyễn Hoàng Anh (2A2202601186)**
- **Loại chiến lược:** FixedSizeChunker tối ưu
- **Tham số:** `FixedSizeChunker(chunk_size=800, overlap=120)`
- **Embedder:** MockEmbedder
- **Số chunk:** 274
- **Lý do chọn:** Kích thước chunk lớn (800) giúp mỗi chunk bao phủ nhiều thông tin hơn, giảm số lượng chunk tổng thể. Overlap cao giữ liên kết giữa các chunk.

### So Sánh Giữa Các Thành Viên

| Thành viên | Chiến lược | Số chunk | Embedder | Điểm mạnh | Điểm yếu |
|-----------|----------|---------|----------|-----------|----------|
| Minh | Recursive(500) | 534 | OpenAI | Giữ cấu trúc đoạn, embedding thật | 534 chunks -> phân mảnh |
| Thịnh Quang | Heading(2000) | 189 | Lexical | Ít chunk, giữ nguyên section | Lexical embedder không đo ngữ nghĩa |
| Nam | FixedSize(800) | 274 | Mock | Chunk lớn, ít phân mảnh | Mock embedder không ngữ nghĩa |
| Duy | Recursive(500) | 534 | OpenAI | Giữ cấu trúc đoạn | 534 chunks -> phân mảnh |
| Hoàng Anh | FixedSize(800) | 274 | Mock | Chunk lớn, ổn định | Mock embedder không ngữ nghĩa |

**Lưu ý:** Minh và Duy dùng chung Recursive(500) + OpenAI, Nam và Hoàng Anh dùng chung FixedSize(800) + Mock. Điều này làm giảm tính đa dạng của so sánh. Khuyến nghị: ít nhất 1 thành viên chuyển sang SentenceChunker hoặc HeadingChunker để có thêm góc nhìn.

**Chiến lược nào tốt nhất cho chủ đề này? Tại sao?**
> Dựa trên số liệu, HeadingRecursiveChunker của Thịnh Quang cho thấy tiềm năng tốt nhất: chỉ 189 chunk (ít nhất) -> ít phân mảnh, chunk_size=2000 giữ trọn điều khoản -> mỗi chunk là một đáp án hoàn chỉnh. Tuy nhiên lexical embedder không phản ánh ngữ nghĩa thực nên kết quả cần kiểm chứng thêm. Với neural embedder (OpenAI), Recursive(500) của Minh/Duy cho kết quả khách quan hơn nhưng bị phân mảnh. Giải pháp lý tưởng: HeadingChunker + OpenAI embedder.

---

## 3. Câu hỏi đánh giá & Chất lượng truy xuất (Retrieval Quality) — Nhóm (10 điểm)

### Câu hỏi đánh giá & Câu trả lời chuẩn (nhóm thống nhất)

> **10 câu hỏi**, đa dạng, có thể kiểm chứng; **2 câu (Q2, Q7)** cần lọc `customer_role: seller`.

| # | Câu hỏi (Query) | Câu trả lời chuẩn (Gold Answer) | Chunk chứa thông tin |
|---|-------|-------------------------------|---------------------|
| 1 | Người mua có những hình thức trả hàng nào? Phí trả hàng ra sao? | 3 hình thức: (1) Đơn vị vận chuyển đến lấy hàng (miễn phí), (2) Trả hàng tại bưu cục (miễn phí), (3) Tự sắp xếp (trả trước phí, Shopee hoàn lại sau). | `tra-hang-phuong-thuc-gui-hoan-tra` mục 1.1 |
| 2 | Hậu quả/chế tài khi người bán vi phạm chính sách cấm sản phẩm? (filter: seller) | (i) Sản phẩm bị xóa, (ii) Tài khoản bị giới hạn/đình chỉ/xóa, (iii) Cấn trừ số dư, (iv) Phong tỏa rút tiền, (v) Phạt hành chính, xử lý hình sự. | `chinh-sach-cam-han-che-san-pham` mục 3 |
| 3 | Người bán KHÔNG được đăng bán những loại sản phẩm nào? | Cấm: phản động, khiêu dâm, bạo lực, hàng giả, vũ khí, chất nổ, ma túy, động vật hoang dã, xâm phạm sở hữu trí tuệ. | `quy-dinh-dang-ban-san-pham` mục B.2 |
| 4 | Shopee thu thập dữ liệu cá nhân người dùng trong trường hợp nào? | Khi đăng ký/sử dụng tài khoản, thực hiện giao dịch, tương tác CSKH, truy cập nền tảng, từ bên thứ ba. | `chinh-sach-bao-mat` mục 2 |
| 5 | Hàng hóa nào KHÔNG được hỗ trợ vận chuyển trên Shopee? | Hàng cấm pháp luật, động vật sống, thực vật tươi, hàng đông lạnh, hàng dễ vỡ, hàng cồng kềnh, chất lỏng dễ cháy nổ. | `chinh-sach-van-chuyen-shopee` mục B |
| 6 | Điều kiện độ tuổi và năng lực pháp lý để sử dụng Shopee? | Từ đủ 18 tuổi hoặc có đồng ý của cha mẹ/người giám hộ. Có năng lực hành vi dân sự đầy đủ. | `dieu-khoan-dich-vu` mục 2 |
| 7 | Chứng từ người bán cần cung cấp khi đăng bán? (filter: seller) | Scan từ bản gốc, không làm giả/chỉnh sửa. Pháp nhân nước ngoài cần Giấy phép kinh doanh. Tuân thủ Luật Thương Mại. | `quy-dinh-dang-ban-san-pham` mục B.1 |
| 8 | Quyền và trách nhiệm các bên trong vận chuyển? | Người bán đóng gói đúng quy cách. Đơn vị vận chuyển giao đúng hạn, bồi thường hư hỏng. Người mua quyền kiểm tra, từ chối nhận. | `chinh-sach-van-chuyen-shopee` mục C |
| 9 | Shopee có chia sẻ dữ liệu cá nhân cho bên thứ ba không? | Có: với công ty liên kết, nhà cung cấp dịch vụ, đối tác (có đồng ý), cơ quan nhà nước, mua bán/sáp nhập. | `chinh-sach-bao-mat` mục 6 |
| 10 | Khi hàng hư hỏng/thất lạc trong vận chuyển, ai bồi thường? | Đơn vị vận chuyển chịu trách nhiệm. Nếu người bán tự vận chuyển thì tự chịu. | `chinh-sach-van-chuyen-shopee` mục C |

### Tổng hợp chất lượng truy xuất của nhóm

| # | Câu hỏi | Minh (Rec500) | Thịnh Quang (Head2000) | Nam (Fix800) | Duy (Rec500) | Hoàng Anh (Fix800) |
|---|---------|-------------|---------------------|------------|------------|------------------|
| 1 | Hình thức trả hàng | Dung 1 phan | Co evidence | Dung 1 phan | Dung 1 phan | Thiếu |
| 2 | Hậu quả vi phạm (filter) | Sai | Co evidence | Sai | Sai | Sai section |
| 3 | Nội dung cấm đăng bán | Sai | Co evidence | Sai | Sai | Sai |
| 4 | Thu thập dữ liệu | Dung chủ đề | Co evidence | Dung 1 phan | Sai khía cạnh | Sai |
| 5 | Hàng không vận chuyển | Dung | Khong co | Dung | Dung | Sai |
| 6 | Điều kiện độ tuổi | Sai nội dung | Co evidence | Dung 1 phan | Sai nội dung | Sai |
| 7 | Chứng từ đăng bán (filter) | Dung 1 phan | Co evidence | Dung 1 phan | Dung 1 phan | Dung |
| 8 | Trách nhiệm vận chuyển | Dung | Co evidence | Dung | Dung | Dung |
| 9 | Chia sẻ dữ liệu | Sai | Co evidence | Sai | Sai | Sai |
| 10 | Bồi thường vận chuyển | Dung 1 phan | Co evidence | Dung 1 phan | Dung 1 phan | Sai |

**Tổng kết điểm (theo snippet matching, mỗi câu 2đ):**

| Thành viên | Chiến lược | Điểm /20 | Evidence Hit@3 |
|-----------|----------|---------|---------------|
| Minh | Recursive(500) + OpenAI | 8 | 6/10 |
| Thịnh Quang | Heading(2000) + Lexical | ~18* | 9/10 |
| Nam | FixedSize(800) + Mock | 10 | 5/10 |
| Duy | Recursive(500) + OpenAI | 8 | 6/10 |
| Hoàng Anh | FixedSize(800) + Mock | 4 | 2/10 |

*Thịnh Quang dùng lexical embedder (không đo ngữ nghĩa thực) nên điểm cao nhưng cần xác nhận lại bằng neural embedder.

### Phân tích A/B Filter (Q2 & Q7)

| Query | Không filter (top-1) | Có filter seller (top-1) | Kết luận |
|-------|---------------------|------------------------|----------|
| Q2: Hậu quả vi phạm | `dieu-khoan-dich-vu` (both) - Sai | `quy-dinh-dang-ban` (seller) - Dung | Filter loại bỏ nhiễu |
| Q7: Chứng từ đăng bán | `chinh-sach-van-chuyen` (both) - Sai | `quy-dinh-dang-ban` (seller) - Dung | Filter loại bỏ nhiễu |

> Filter metadata `customer_role` có giá trị cao trong việc loại bỏ tài liệu sai đối tượng. Tuy nhiên filter không giải quyết được vấn đề chunk quá nhỏ/phân mảnh.

### Phân Tích Lỗi (Failure Analysis) — 3 Trường Hợp

#### Failure Case 1: Q2 — Chunk penalty ngoài top-3 (Minh, Duy, Nam, Hoang Anh)
- **Query:** "Hậu quả/chế tài khi vi phạm chính sách cấm sản phẩm?"
- **Nguyên nhân:** Mục 3 của `chinh-sach-cam-han-che-san-pham` bị Recursive/FixedSize cắt thành nhiều chunk nhỏ. Chunk chứa penalty list xếp hạng ngoài top-3. Chỉ Thịnh Quang với chunk_size=2000 giữ được toàn bộ section.
- **Đề xuất:** Tăng chunk_size >= 1000 hoặc dùng HeadingChunker.

#### Failure Case 2: Q9 — Nhầm lẫn "thu thập" vs "chia sẻ" (Tất cả trừ Thịnh Quang)
- **Query:** "Shopee có chia sẻ dữ liệu cá nhân cho bên thứ ba không?"
- **Nguyên nhân:** Embedding không phân biệt "thu thập" (section 2) và "chia sẻ" (section 6) — cả hai đều chứa "dữ liệu cá nhân", "bên thứ ba". Top-1-3 trả về chunk sai section.
- **Đề xuất:** (a) Thêm metadata section để filter chính xác; (b) Dùng embedder mạnh hơn (text-embedding-3-large, 3072d).

#### Failure Case 3: Q3 — Danh sách cấm bị phân mảnh (Minh, Duy, Nam, Hoang Anh)
- **Query:** "Người bán không được đăng bán những loại sản phẩm nào?"
- **Nguyên nhân:** Section B.2 của `quy-dinh-dang-ban` liệt kê dài các nội dung cấm. Với chunk_size=500 hoặc 800, section bị cắt thành nhiều chunk, không chunk nào chứa đủ danh sách.
- **Đề xuất:** Dùng HeadingChunker giữ trọn section B.2 làm 1 chunk.

---

## 4. Thuyết trình (Demo) & Bài học nhóm — Nhóm (5 điểm)

**Những phân tích (insights) hay nhất nhóm sẽ trình bày:**

1. **Chiến lược chunking quyết định precision:** HeadingChunker(2000) của Thịnh Quang cho Evidence Hit@3 cao nhất (9/10) dù dùng lexical embedder. Điều này chứng minh chunk coherence (tính mạch lạc) quan trọng hơn embedding model trong retrieval chất lượng.

2. **Metadata filter có giá trị thực sự:** Q2 và Q7 chứng minh filter `customer_role: seller` loại bỏ nhiễu hiệu quả — top-1 chuyển từ sai sang đúng khi bật filter.

3. **Cosine similarity không phân biệt được sắc thái:** Q9 thất bại trên 4/5 thành viên vì embedding gộp "thu thập" và "chia sẻ" dữ liệu thành cùng một chủ đề.

**Bài học rút ra khi so sánh trong nhóm:**

> Cùng corpus, cùng query, khác chunker -> kết quả retrieval khác biệt rõ rệt (4/20 đến 18/20). Chiến lược chunking quyết định thông tin có "sống sót" qua bước embedding hay không. Chunk quá nhỏ (500) -> phân mảnh, mất thông tin. Chunk lớn + giữ cấu trúc (2000, heading) -> giữ trọn vẹn điều khoản, precision cao hơn. Mock embedder không phản ánh chất lượng thực -> cần neural embedder để benchmark có ý nghĩa.

**Nếu làm lại, nhóm sẽ thay đổi gì trong chiến lược dữ liệu (data strategy)?**

1. **Dùng HeadingChunker + OpenAI embedder:** Kết hợp ưu điểm của Thịnh Quang (chunk theo section, ít chunk) với neural embedder của Minh/Duy (ngữ nghĩa thực).
2. **Tăng chunk_size lên 1000-2000:** Phù hợp với văn bản chính sách — mỗi điều khoản thường 600-2000 ký tự.
3. **Thêm metadata `section`:** Gắn tiêu đề mục vào mỗi chunk để filter chính xác theo chương/điều khoản.
4. **Dùng embedder mạnh hơn:** `text-embedding-3-large` (3072d) thay vì `text-embedding-3-small` (1536d) để phân biệt ngữ nghĩa tinh tế.
5. **Thống nhất embedder:** Tất cả thành viên dùng cùng OpenAI embedder để so sánh công bằng (mock không phản ánh chất lượng thực).

---

## Tự Đánh Giá (Phần Nhóm)

| Tiêu chí | Điểm tự đánh giá |
|----------|-------------------|
| Lựa chọn tài liệu (Document Set Quality) | 10 / 10 |
| Thiết kế chiến lược (Strategy Design) | 13 / 15 |
| Chất lượng truy xuất (Retrieval Quality) | 8 / 10 |
| Thuyết trình (Demo) | 5 / 5 |
| **Tổng phần nhóm** | **36 / 40** |

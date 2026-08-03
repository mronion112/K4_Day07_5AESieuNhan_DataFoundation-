# Báo Cáo Nhóm — Lab 7: Embedding & Vector Store

**Nhóm:** 5AE Siêu Nhân
**Thành viên:** Trần Quang Minh
**Ngày:** 03/08/2026

> **Nộp 1 bản / nhóm.** Phần cá nhân (hướng tiếp cận, kết quả riêng, dự đoán…) mỗi thành viên nộp riêng trong `REPORT_CANHAN.md`. Chi tiết thang điểm: `docs/SCORING.md`.

**Tổng điểm phần nhóm: 40** = Lựa chọn tài liệu (10) + Thiết kế chiến lược (15) + Chất lượng truy xuất (10) + Thuyết trình (5).

---

## 1. Lựa chọn tài liệu (Document Set Quality) — Nhóm (10 điểm)

### Phạm vi bộ tài liệu (Scope)

**Chủ đề (cố định theo lớp K4):** Chính sách thương mại điện tử / hỗ trợ khách hàng (thanh toán, đổi trả, giao hàng, quyền riêng tư, điều kiện người bán…).

**Phạm vi cụ thể nhóm tập trung:**
> Toàn bộ chính sách TMĐT Shopee: điều khoản dịch vụ, bảo mật, đăng bán sản phẩm, sản phẩm cấm, vận chuyển, trả hàng & phí hoàn trả. Nguồn: help.shopee.vn (robots.txt cho phép).

### Danh sách tài liệu (Data Inventory)

| # | Tên tài liệu | Nguồn (Source URL) | Ngày lấy / Phiên bản | Số ký tự | Metadata đã gán |
|---|--------------|------------|--------------------|----------|-----------------|
| 1 | Chính sách bảo mật | help.shopee.vn/portal/4/article/77244 | 03/08/2026 / not-stated | 42,849 | `customer_role: both`, `category: privacy` |
| 2 | Chính sách cấm/hạn chế sản phẩm | help.shopee.vn/portal/4/article/77247 | 03/08/2026 / not-stated | 10,034 | `customer_role: seller`, `category: listing` |
| 3 | Chính sách vận chuyển Shopee | help.shopee.vn/portal/4/article/77484 | 03/08/2026 / not-stated | 22,413 | `customer_role: both`, `category: shipping` |
| 4 | Điều khoản dịch vụ | help.shopee.vn/portal/4/article/77243 | 03/08/2026 / not-stated | 83,051 | `customer_role: both`, `category: terms` |
| 5 | Quy định về đăng bán sản phẩm | help.shopee.vn/portal/4/article/77246 | 03/08/2026 / not-stated | 21,315 | `customer_role: seller`, `category: listing` |
| 6 | Phương thức gửi hàng hoàn trả & phí | help.shopee.vn/portal/4/article/189477 | 03/08/2026 / not-stated | 5,713 | `customer_role: buyer`, `category: returns` |

**Danh sách kiểm tra quản trị dữ liệu (Data governance checklist):**
- [x] Tập tài liệu (Corpus) chỉ chứa nguồn công khai/được phép dùng và không chứa dữ liệu cá nhân, thông tin đăng nhập hoặc tài liệu nội bộ.
- [x] Mỗi tài liệu có `source_url`, `retrieved_at`, `document_version` (hoặc ngày hiệu lực) trong metadata.

### Cấu trúc Metadata (Metadata Schema)

| Trường metadata | Kiểu | Ví dụ giá trị | Tại sao hữu ích cho truy xuất (retrieval)? |
|----------------|------|---------------|-------------------------------|
| `customer_role` | string | `buyer`, `seller`, `both` | Bắt buộc K4: phân biệt chính sách cho người mua/người bán, dùng để filter query như "quy định cho người bán" |
| `category` | string | `privacy`, `listing`, `shipping`, `terms`, `returns` | Phân loại chủ đề chính sách, giúp lọc nhanh khi câu hỏi thuộc một lĩnh vực cụ thể |
| `source_url` | string | URL Shopee Help Center | Truy vết nguồn gốc, kiểm tra tính xác thực của câu trả lời |
| `retrieved_at` | string | `2026-08-03` | Kiểm tra độ mới của dữ liệu, phát hiện tài liệu lỗi thời |
| `document_version` | string | `not-stated` | Phiên bản chính sách, quan trọng khi có thay đổi qua thời gian |
| `language` | string | `vi` | Lọc ngôn ngữ, tránh trộn tài liệu đa ngôn ngữ |

---

## 2. Thiết kế chiến lược (Strategy Design) — Nhóm (15 điểm)

> Mỗi thành viên thử **một chiến lược khác nhau** trên cùng bộ tài liệu; nhóm tổng hợp và so sánh ở đây.

### Phân tích đường cơ sở (Baseline Analysis)

Chạy `ChunkingStrategyComparator().compare()` trên 2-3 tài liệu:

| Tài liệu | Chiến lược (Strategy) | Số lượng Chunk | Độ dài trung bình | Giữ được ngữ cảnh không? |
|-----------|----------|-------------|------------|-------------------|
| dieu-khoan-dich-vu (83K chars) | FixedSizeChunker | 238 | 399 | ⚠️ Cắt giữa câu, mất ngữ cảnh pháp lý |
| | SentenceChunker | 160 | 517 | ❌ Chunk lên tới 5,285 chars, vượt embedding |
| | RecursiveChunker | 321 | 257 | ✅ Ưu tiên đoạn văn, không vượt ngưỡng |
| quy-dinh-dang-ban-san-pham (21K) | FixedSizeChunker | 61 | 399 | ⚠️ Đều nhưng cắt ngang danh sách liệt kê |
| | SentenceChunker | 79 | 268 | ✅ Câu ngắn hơn, chunk đều hơn |
| | RecursiveChunker | 68 | 311 | ✅ Giữ cấu trúc A/B/C rõ ràng |
| tra-hang-phuong-thuc-gui-hoan-tra (5.7K) | FixedSizeChunker | 17 | 383 | ✅ Tài liệu ngắn, ít bị ảnh hưởng |
| | SentenceChunker | 9 | 633 | ⚠️ 9 chunk, ít nhất là tốt nhưng chunk vượt 500 |
| | RecursiveChunker | 18 | 315 | ✅ Cân bằng nhất cho tài liệu ngắn |

### Chiến lược của từng thành viên

**Thành viên 1 — Trần Quang Minh**
- **Loại chiến lược:** RecursiveChunker tinh chỉnh
- **Mô tả & lý do chọn cho chủ đề này:** Chọn RecursiveChunker vì văn bản chính sách có cấu trúc phân cấp rõ ràng (đoạn → dòng → câu). Bỏ separator `""` (ký tự) để không bao giờ cắt giữa từ. Tăng `chunk_size=500` để mỗi chunk chứa đủ ngữ cảnh cho embedding, đồng thời bao phủ được toàn bộ một điều khoản nhỏ. Lý do: FixedSize cắt ngang câu gây mất mạch lạc; Sentence tạo chunk quá dài với văn bản pháp lý tiếng Việt.
- **Code snippet:** `RecursiveChunker(separators=["\n\n", "\n", ". ", " "], chunk_size=500)`

**Thành viên 2 — [Tên]**
- **Loại chiến lược:**
- **Mô tả & lý do chọn:**
- **Code snippet (nếu custom):**

**Thành viên 3 — [Tên]**
- **Loại chiến lược:**
- **Mô tả & lý do chọn:**
- **Code snippet (nếu custom):**

### So Sánh Giữa Các Thành Viên

| Thành viên | Chiến lược (Strategy) | Điểm truy xuất (/10) | Điểm mạnh | Điểm yếu |
|-----------|----------|----------------------|-----------|----------|
| Trần Quang Minh | RecursiveChunker(500) | 8/20 | Giữ cấu trúc đoạn, không chunk nào vượt 500 | 534 chunks → thông tin bị phân mảnh, Q2-Q3-Q4-Q9 thất bại |
| [Tên 2] | | | | |
| [Tên 3] | | | | |

**Chiến lược nào tốt nhất cho chủ đề này? Tại sao?**
> RecursiveChunker bỏ separator ký tự với chunk_size=500 là lựa chọn cân bằng: không cắt giữa từ, tôn trọng ranh giới đoạn văn và câu. Tuy nhiên tạo quá nhiều chunk (534) khiến thông tin bị phân mảnh — câu trả lời nằm trong chunk thứ 5-6 thay vì top-3. Giải pháp tiềm năng: tăng chunk_size lên 800 hoặc dùng HeadingChunker tách theo điều khoản để mỗi chunk là một đơn vị ngữ nghĩa trọn vẹn.

---

## 3. Câu hỏi đánh giá & Chất lượng truy xuất (Retrieval Quality) — Nhóm (10 điểm)

### Câu hỏi đánh giá & Câu trả lời chuẩn (nhóm thống nhất)

> **Đúng 5 câu hỏi**, đa dạng, có thể kiểm chứng; **ít nhất 1 câu** cần lọc metadata mới trả lời tốt. Đây là bộ câu hỏi chung cho mọi thành viên chạy.

| # | Câu hỏi (Query) | Câu trả lời chuẩn (Gold Answer) | Chunk nào chứa thông tin? |
|---|-------|-------------------------------|--------------------------|
| 1 | Người mua có những hình thức trả hàng nào khi yêu cầu Trả hàng/Hoàn tiền được chấp nhận? Phí trả hàng được tính ra sao? | Có 3 hình thức: (1) Đơn vị vận chuyển đến lấy hàng (miễn phí), (2) Trả hàng tại bưu cục (miễn phí), (3) Tự sắp xếp (người mua trả trước phí, Shopee hoàn lại sau). Với 2 hình thức đầu, người mua cần đóng gói hàng, dán mã vận đơn. Với hình thức tự sắp xếp cần thanh toán trước phí và đăng tải bằng chứng trả hàng. | `tra-hang-phuong-thuc-gui-hoan-tra` mục 1.1 |
| 2 | Những hậu quả/chế tài nào có thể áp dụng nếu người bán vi phạm chính sách cấm/hạn chế sản phẩm trên Shopee? ⚠️ Cần filter `customer_role: seller` | Người bán có thể bị: (i) sản phẩm bị xóa, (ii) tài khoản bị giới hạn quyền, (iii) tài khoản bị đình chỉ hoặc xóa, (iv) cấn trừ số dư tài khoản/phong tỏa quyền rút tiền, (v) các chế tài khác theo pháp luật như phạt hành chính, xử lý hình sự, bồi thường thiệt hại. | `chinh-sach-cam-han-che-san-pham` mục 3 |
| 3 | Người bán KHÔNG được phép đăng bán những loại nội dung/sản phẩm nào trên Shopee? | Nghiêm cấm đăng tải: (a) sản phẩm phản động, chống phá, bài xích tôn giáo, khiêu dâm, bạo lực, đi ngược lại thuần phong mỹ tục Việt Nam, xâm phạm chủ quyền quốc gia; (b) thông tin rác, phá hoại; (c) hàng giả, hàng nhái, hàng vi phạm sở hữu trí tuệ; (d) vũ khí, chất nổ, chất gây nghiện; (e) động vật hoang dã quý hiếm. Ngoài ra còn danh sách hàng hóa bị cấm/hạn chế chi tiết at Chính sách cấm/hạn chế sản phẩm. | `quy-dinh-dang-ban-san-pham` mục B.2 |
| 4 | Shopee thu thập dữ liệu cá nhân của người dùng trong những trường hợp nào? | Shopee thu thập dữ liệu cá nhân khi: (a) người dùng đăng ký/sử dụng Dịch Vụ hoặc Tài Khoản; (b) người dùng thực hiện giao dịch; (c) người dùng tương tác với dịch vụ chăm sóc khách hàng; (d) người dùng truy cập/duyệt Nền tảng; (e) từ bên thứ ba (đối tác, dịch vụ thanh toán, mạng xã hội khi liên kết tài khoản). | `chinh-sach-bao-mat` mục 2 |
| 5 | Những loại hàng hóa nào KHÔNG được hỗ trợ vận chuyển trên Shopee? | Không hỗ trợ vận chuyển: hàng cấm theo quy định pháp luật (ma túy, vũ khí, chất nổ, chất cháy, hàng quốc cấm), động vật sống, thực vật tươi, hàng đông lạnh cần bảo quản đặc biệt, hàng hóa dễ vỡ không đóng gói đúng quy cách, hàng cồng kềnh vượt kích thước/trọng lượng quy định, hàng có mùi, chất lỏng dễ cháy nổ. | `chinh-sach-van-chuyen-shopee` mục B |
| 6 | Người dùng cần đáp ứng điều kiện gì về độ tuổi và năng lực pháp lý để sử dụng dịch vụ Shopee? | Người dùng phải từ đủ 18 tuổi trở lên hoặc có sự giám sát/đồng ý của cha mẹ/người giám hộ hợp pháp. Người dùng phải có năng lực hành vi dân sự đầy đủ để giao kết hợp đồng. Nếu đại diện cho tổ chức, phải có thẩm quyền ràng buộc tổ chức đó. | `dieu-khoan-dich-vu` mục 2 |
| 7 | Người bán cần cung cấp những chứng từ gì và tuân thủ quy định nào khi đăng bán sản phẩm trên Shopee? ⚠️ Cần filter `customer_role: seller` | Tất cả chứng từ phải được scan từ bản gốc, không được làm giả/chỉnh sửa/tẩy xóa. Người bán phải tuân thủ Điều 117, 120.4, 121 Luật Thương Mại về hoạt động trưng bày/giới thiệu hàng hóa. Người bán là pháp nhân có vốn đầu tư nước ngoài cần có Giấy phép kinh doanh phù hợp. | `quy-dinh-dang-ban-san-pham` mục B.1 |
| 8 | Quyền và trách nhiệm của các bên (người mua, người bán, đơn vị vận chuyển) liên quan đến vận chuyển hàng hóa trên Shopee được quy định như thế nào? | Người bán chịu trách nhiệm đóng gói hàng đúng quy cách, cung cấp thông tin chính xác. Đơn vị vận chuyển chịu trách nhiệm giao hàng đúng thời gian, bảo quản hàng hóa nguyên vẹn, bồi thường khi hư hỏng/mất mát. Người mua có quyền kiểm tra hàng khi nhận, từ chối nhận nếu không đúng. Shopee hỗ trợ giải quyết khiếu nại. Chính sách này không áp dụng khi người bán tự tổ chức vận chuyển. | `chinh-sach-van-chuyen-shopee` mục C |
| 9 | Shopee có chia sẻ dữ liệu cá nhân của người dùng cho bên thứ ba không? Trong trường hợp nào? | Shopee có thể chia sẻ dữ liệu cá nhân trong các trường hợp: (a) với công ty liên kết/con để cung cấp Dịch Vụ; (b) với nhà cung cấp dịch vụ bên thứ ba (thanh toán, vận chuyển, xác thực, marketing); (c) với đối tác kinh doanh khi có sự đồng ý; (d) theo yêu cầu của cơ quan nhà nước có thẩm quyền/tuân thủ pháp luật; (e) trong trường hợp mua bán/sáp nhập công ty. Shopee cam kết yêu cầu bên nhận bảo mật tương đương. | `chinh-sach-bao-mat` mục 6 |
| 10 | Khi hàng hóa bị hư hỏng hoặc thất lạc trong quá trình vận chuyển, trách nhiệm bồi thường thuộc về ai và được xử lý như thế nào? | Đơn vị vận chuyển chịu trách nhiệm bồi thường khi hàng hóa bị hư hỏng/mất mát trong quá trình vận chuyển. Mức bồi thường theo quy định của từng đơn vị vận chuyển, tối đa theo giá trị đơn hàng. Người mua/người bán có thể gửi khiếu nại qua Shopee. Shopee sẽ phối hợp với đơn vị vận chuyển để giải quyết. Đối với trường hợp người bán tự tổ chức vận chuyển, người bán tự chịu trách nhiệm. | `chinh-sach-van-chuyen-shopee` mục C kết hợp `dieu-khoan-dich-vu` |

### Tổng hợp chất lượng truy xuất của nhóm

> Cách chấm (theo `docs/SCORING.md`): **2 điểm/câu** — top-3 chứa chunk liên quan + agent trả lời đúng (2), có liên quan nhưng thiếu/không ở top-1 (1), không có trong top-3 (0).

| # | Câu hỏi | Chiến lược tốt nhất cho câu này | Có chunk liên quan trong top-3? | Ghi chú |
|---|---------|-------------------------------|-------------------------------|---------|
| 1 | Hình thức trả hàng | Recursive (hiện tại) | ✅ Có (1/3 chunk liên quan, thiếu 2 snippet) | Top-1 đúng doc, nhưng chỉ chứa 1/3 snippet |
| 2 | Hậu quả vi phạm cấm sản phẩm 🔍 | Recursive (hiện tại) | ❌ Không | Chunk chứa penalty list ở vị trí #5+, ngoài top-3. **FAILURE CASE** |
| 3 | Nội dung cấm đăng bán | Recursive (hiện tại) | ❌ Không | Top-3 đúng doc nhưng chunk không chứa danh sách cấm cụ thể. **FAILURE CASE** |
| 4 | Thu thập dữ liệu cá nhân | Recursive (hiện tại) | ❌ Không (chunk đúng chủ đề, không đúng nội dung) | Chunk nói về "loại dữ liệu thu thập" chứ không phải "khi nào thu thập" |
| 5 | Hàng không vận chuyển | Recursive (hiện tại) | ✅ Có (2/3 chunk) | Truy xuất tốt, score 0.77, thông tin tập trung trong 1 section |
| 6 | Điều kiện độ tuổi | Recursive (hiện tại) | ⚠️ 1/3 chunk có snippet "người giám hộ" | Top-1 về "trẻ em dưới 13 tuổi" thay vì "đủ 18 tuổi" - sai nội dung |
| 7 | Chứng từ đăng bán 🔍 | Recursive (hiện tại) | ✅ Có (2/3 chunk) | Top-1 không phải doc gold (vận chuyển), nhưng top-2-3 đúng |
| 8 | Trách nhiệm vận chuyển | Recursive (hiện tại) | ✅ Có (3/3 chunk, 2 snippets) | Truy xuất tốt nhất, score 0.68-0.64, 3/3 cùng doc |
| 9 | Chia sẻ dữ liệu bên thứ ba | Recursive (hiện tại) | ❌ Không | Chunk nói về "thu thập" thay vì "chia sẻ" - nhầm lẫn ngữ nghĩa. **FAILURE CASE** |
| 10 | Bồi thường vận chuyển | Recursive (hiện tại) | ⚠️ 1/3 chunk có snippet "hư hỏng" | Score thấp 0.55, chunk không chứa đầy đủ quy trình bồi thường |

**Tổng điểm: 8/20** (chấm theo tiêu chí snippet matching)

**Lọc bằng metadata có giúp ích không? Ở câu hỏi nào?**
> **Q2 (filter `seller`)**: Không có filter → top-1 là `dieu-khoan-dich-vu` (both). Có filter → top-1 là `quy-dinh-dang-ban-san-pham` (seller). Filter giúp LOẠI BỎ tài liệu không liên quan (`dieu-khoan-dich-vu` không có penalty list cho sản phẩm cấm). Tuy nhiên filter không cải thiện được việc tìm đúng chunk — chunk penalty vẫn ở ngoài top-3.
>
> **Q7 (filter `seller`)**: Không có filter → top-1 là `chinh-sach-van-chuyen-shopee` (both) vì chứa từ "chứng từ". Có filter → top-1 là `quy-dinh-dang-ban-san-pham` (seller). Filter LOẠI BỎ `chinh-sach-van-chuyen` (nhiễu) và đưa đúng doc seller lên top.
>
> **Kết luận**: Filter metadata có giá trị cao trong việc LOẠI NHIỄU (loại bỏ doc sai đối tượng), nhưng KHÔNG giải quyết được vấn đề chunk quá nhỏ/phân mảnh. Filter + chunk lớn hơn mới là giải pháp toàn diện.

---

## 4. Thuyết trình (Demo) & Bài học nhóm — Nhóm (5 điểm)

**Những phân tích (insights) hay nhất nhóm sẽ trình bày:**
> 1. **RecursiveChunker tạo quá nhiều chunk với văn bản pháp lý dài**: 534 chunks từ 6 tài liệu → thông tin câu trả lời bị phân mảnh qua 5-10 chunk, chỉ 2-3 lọt vào top-k → precision thấp (8/20).
> 2. **Metadata filter có giá trị thực sự**: Q2 và Q7 chứng minh filter `customer_role: seller` loại bỏ được nhiễu từ doc `both`, cải thiện top-1 từ sai thành đúng.
> 3. **Cosine similarity không phân biệt được "thu thập" vs "chia sẻ" dữ liệu**: Q4 và Q9 có cùng doc nguồn nhưng hỏi 2 khía cạnh khác nhau → retrieval trả về chunk về "thu thập" cho cả 2 câu → embedding model không đủ tinh tế để phân biệt.

**Bài học rút ra khi so sánh trong nhóm:**
> Cùng corpus, cùng embedder, chỉ khác chunker → kết quả retrieval khác biệt rõ rệt. Chiến lược chunking quyết định việc thông tin có "sống sót" qua bước embedding và lọt vào top-k hay không. Recursive giữ được cấu trúc nhưng tạo quá nhiều mảnh nhỏ; FixedSize ổn định nhưng mất mạch lạc; HeadingChunker (dự kiến) sẽ cho chunk trọn vẹn nhất về ngữ nghĩa.

**Nếu làm lại, nhóm sẽ thay đổi gì trong chiến lược dữ liệu (data strategy)?**
> 1. **Tăng chunk_size lên 800-1000**: Với văn bản chính sách, mỗi điều khoản thường 600-1000 ký tự. Chunk lớn hơn = ít chunk hơn = ít phân mảnh = precision cao hơn.
> 2. **Dùng HeadingChunker**: Tách theo cấu trúc A./1./1.1 thay vì theo ký tự. Mỗi điều khoản là một chunk → retrieval chính xác hơn vì mỗi chunk đã là một câu trả lời hoàn chỉnh.
> 3. **Thêm metadata `section` hoặc `heading`**: Gắn tiêu đề section vào mỗi chunk để search_with_filter có thể lọc theo chương/mục, không chỉ theo `customer_role`.
> 4. **Dùng embedder mạnh hơn**: `text-embedding-3-large` (3072 chiều) thay vì `text-embedding-3-small` (1536 chiều) để phân biệt ngữ nghĩa tinh tế hơn (vd: "thu thập" vs "chia sẻ").

### Phân Tích Lỗi (Failure Analysis) — 3 Trường Hợp

#### Failure Case 1: Q2 — Chunk penalty nằm ngoài top-3
- **Query**: "Những hậu quả/chế tài nào nếu người bán vi phạm chính sách cấm sản phẩm?"
- **Nguyên nhân**: Mục 3 của `chinh-sach-cam-han-che-san-pham` liệt kê 5 chế tài: (i) sản phẩm bị xóa, (ii) tài khoản bị đình chỉ, (iii) cấn trừ số dư... Section này bị RecursiveChunker cắt thành 2-3 chunk nhỏ. Chunk chứa penalty list xếp hạng #5 (score 0.49) — ngoài top-3. Các chunk top-1 đến top-3 đến từ `quy-dinh-dang-ban` và `dieu-khoan-dich-vu` nói chung chung về "vi phạm" nhưng không có danh sách chế tài cụ thể.
- **Bằng chứng**: Top-1 "Tuyên truyền về những thông tin mà pháp luật nghiêm cấm" (đúng chủ đề, sai nội dung). Top-4 "[4] score=0.50 doc=chinh-sach-cam-han-che-san-pham" nói về hàng vi phạm bản quyền, không phải chế tài.
- **Đề xuất**: Tăng chunk_size lên 800-1000 để toàn bộ section 3 nằm gọn trong 1 chunk.

#### Failure Case 2: Q3 — Danh sách cấm bị phân mảnh
- **Query**: "Người bán KHÔNG được phép đăng bán những loại nội dung/sản phẩm nào?"
- **Nguyên nhân**: Section B.2 của `quy-dinh-dang-ban` liệt kê dài các nội dung cấm (phản động, khiêu dâm, bạo lực, hàng giả...). RecursiveChunker cắt section này thành nhiều chunk. Top-5 toàn là chunk từ `quy-dinh-dang-ban` nhưng không chunk nào chứa danh sách cấm — chúng chứa các phần khác như "chứng từ", "khuyến cáo", "hình ảnh sản phẩm".
- **Bằng chứng**: Top-1 "c. Tất cả chứng từ..." (score 0.64) — nói về chứng từ, không phải nội dung cấm. Top-4 "d. Hình ảnh không chứa yếu tố ghê rợn..." (score 0.59) — nói về hình ảnh, không phải danh sách cấm toàn diện.
- **Đề xuất**: Dùng HeadingChunker để giữ trọn section B.2 làm 1 chunk.

#### Failure Case 3: Q9 — Nhầm lẫn "thu thập" vs "chia sẻ"
- **Query**: "Shopee có chia sẻ dữ liệu cá nhân của người dùng cho bên thứ ba không?"
- **Nguyên nhân**: Cả section 2 ("thu thập") và section 6 ("chia sẻ") của `chinh-sach-bao-mat` đều chứa từ "dữ liệu cá nhân" và "bên thứ ba" → embedding không phân biệt được 2 khía cạnh. Top-1-3 đều là chunk về "thu thập dữ liệu" (section 2-3) thay vì "chia sẻ với bên thứ ba" (section 6).
- **Bằng chứng**: Top-1 "3.1. Trừ trường hợp được quy định khác đi...dữ liệu cá nhân mà Shopee có thể thu thập..." (score 0.71) — đúng doc, sai section.
- **Đề xuất**: (a) Thêm metadata section cho phép search_with_filter theo `category: privacy` + `section: sharing`; (b) Dùng embedder mạnh hơn; (c) Query rõ ràng hơn: "Shopee chia sẻ dữ liệu cá nhân trong trường hợp NÀO" thay vì "có...không".

---

## Tự Đánh Giá (Phần Nhóm)

| Tiêu chí | Điểm tự đánh giá |
|----------|-------------------|
| Lựa chọn tài liệu (Document Set Quality) | 10 / 10 |
| Thiết kế chiến lược (Strategy Design) | 12 / 15 |
| Chất lượng truy xuất (Retrieval Quality) | 7 / 10 |
| Thuyết trình (Demo) | 5 / 5 |
| **Tổng phần nhóm** | **34 / 40** |

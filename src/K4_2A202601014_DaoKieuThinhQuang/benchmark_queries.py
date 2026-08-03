from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True)
class BenchmarkCase:
    query: str
    gold_answer: str
    expected_doc_id: str
    expected_section: str
    evidence_groups: tuple[tuple[str, ...], ...]
    metadata_filter: dict[str, str] | None = field(default=None)


# Fixed benchmark set selected from message.txt. Do not change after running a
# strategy, otherwise comparisons between team members would not be fair.
BENCHMARK_CASES = [
    BenchmarkCase(
        query=(
            "Người mua có những hình thức trả hàng nào khi yêu cầu Trả hàng/Hoàn tiền "
            "được chấp nhận? Phí trả hàng được tính ra sao?"
        ),
        gold_answer=(
            "Có 3 hình thức: (1) Đơn vị vận chuyển đến lấy hàng (miễn phí), "
            "(2) Trả hàng tại bưu cục (miễn phí), (3) Tự sắp xếp (người mua "
            "trả trước phí, Shopee hoàn lại sau). Với 2 hình thức đầu, người mua "
            "cần đóng gói hàng, dán mã vận đơn. Với hình thức tự sắp xếp cần thanh "
            "toán trước phí và đăng tải bằng chứng trả hàng."
        ),
        expected_doc_id="tra-hang-phuong-thuc-gui-hoan-tra",
        expected_section="mục 1.1 và mục 2.2",
        evidence_groups=(
            ("đơn vị vận chuyển đến lấy hàng",),
            ("trả hàng tại bưu cục",),
            ("tự sắp xếp",),
            ("miễn phí trả hàng",),
            ("thanh toán trước phí trả hàng",),
        ),
        metadata_filter={"customer_role": "buyer"},
    ),
    BenchmarkCase(
        query=(
            "Những hậu quả/chế tài nào có thể áp dụng nếu người bán vi phạm chính "
            "sách cấm/hạn chế sản phẩm trên Shopee?"
        ),
        gold_answer=(
            "Người bán có thể bị: (i) sản phẩm bị xóa, (ii) tài khoản bị giới hạn "
            "quyền, (iii) tài khoản bị đình chỉ hoặc xóa, (iv) cấn trừ số dư tài "
            "khoản/phong tỏa quyền rút tiền, (v) các chế tài khác theo pháp luật như "
            "phạt hành chính, xử lý hình sự, bồi thường thiệt hại."
        ),
        expected_doc_id="chinh-sach-cam-han-che-san-pham",
        expected_section="mục 3",
        evidence_groups=(
            ("sản phẩm bị xóa",),
            ("tài khoản bị giới hạn quyền",),
            ("tài khoản bị đình chỉ",),
            ("phong tỏa quyền rút tiền",),
            ("xử lý hình sự",),
        ),
        metadata_filter={"customer_role": "seller"},
    ),
    BenchmarkCase(
        query="Người bán KHÔNG được phép đăng bán những loại nội dung/sản phẩm nào trên Shopee?",
        gold_answer=(
            "Nghiêm cấm đăng tải: (a) sản phẩm phản động, chống phá, bài xích tôn "
            "giáo, khiêu dâm, bạo lực, đi ngược lại thuần phong mỹ tục Việt Nam, xâm "
            "phạm chủ quyền quốc gia; (b) thông tin rác, phá hoại; (c) hàng giả, hàng "
            "nhái, hàng vi phạm sở hữu trí tuệ; (d) vũ khí, chất nổ, chất gây nghiện; "
            "(e) động vật hoang dã quý hiếm. Ngoài ra còn danh sách hàng hóa bị "
            "cấm/hạn chế chi tiết at Chính sách cấm/hạn chế sản phẩm."
        ),
        expected_doc_id="quy-dinh-dang-ban-san-pham",
        expected_section="mục B.2",
        evidence_groups=(
            ("phản động, chống phá",),
            ("đăng thông tin rác",),
            ("hàng giả", "hàng nhái", "vi phạm quyền sở hữu trí tuệ"),
            ("vũ khí", "chất nổ", "chất gây nghiện"),
            ("động vật hoang dã",),
        ),
        metadata_filter={"customer_role": "seller"},
    ),
    BenchmarkCase(
        query="Shopee thu thập dữ liệu cá nhân của người dùng trong những trường hợp nào?",
        gold_answer=(
            "Shopee thu thập dữ liệu cá nhân khi: (a) người dùng đăng ký/sử dụng Dịch Vụ "
            "hoặc Tài Khoản; (b) người dùng thực hiện giao dịch; (c) người dùng tương "
            "tác với dịch vụ chăm sóc khách hàng; (d) người dùng truy cập/duyệt Nền "
            "tảng; (e) từ bên thứ ba (đối tác, dịch vụ thanh toán, mạng xã hội khi "
            "liên kết tài khoản)."
        ),
        expected_doc_id="chinh-sach-bao-mat",
        expected_section="mục 2",
        evidence_groups=(
            ("đăng ký và/hoặc sử dụng",),
            ("thực hiện các giao dịch",),
            ("tương tác với chúng tôi",),
            ("các bên thứ ba",),
        ),
    ),
    BenchmarkCase(
        query="Những loại hàng hóa nào KHÔNG được hỗ trợ vận chuyển trên Shopee?",
        gold_answer=(
            "Không hỗ trợ vận chuyển: hàng cấm theo quy định pháp luật (ma túy, vũ khí, "
            "chất nổ, chất cháy, hàng quốc cấm), động vật sống, thực vật tươi, hàng "
            "đông lạnh cần bảo quản đặc biệt, hàng hóa dễ vỡ không đóng gói đúng quy "
            "cách, hàng cồng kềnh vượt kích thước/trọng lượng quy định, hàng có mùi, "
            "chất lỏng dễ cháy nổ."
        ),
        expected_doc_id="chinh-sach-van-chuyen-shopee",
        expected_section="mục B",
        evidence_groups=(
            ("ma túy", "vũ khí", "chất nổ", "hàng quốc cấm"),
            ("động vật sống",),
            ("thực vật tươi",),
            ("hàng đông lạnh",),
            ("hàng hóa dễ vỡ", "hàng dễ vỡ"),
            ("hàng cồng kềnh",),
            ("hàng có mùi",),
            ("chất lỏng dễ cháy nổ",),
        ),
    ),
]

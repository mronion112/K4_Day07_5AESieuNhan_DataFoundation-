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


# Đúng 5 query chung đã chốt trong REPORT_NHOM.md.
BENCHMARK_CASES = [
    BenchmarkCase(
        query=(
            "Người mua có những hình thức trả hàng nào khi yêu cầu Trả hàng/Hoàn tiền "
            "được chấp nhận? Phí trả hàng được tính ra sao?"
        ),
        gold_answer=(
            "Có 3 hình thức: đơn vị vận chuyển đến lấy hàng (miễn phí), trả hàng tại "
            "bưu cục (miễn phí), và tự sắp xếp (người mua thanh toán trước, Shopee "
            "hỗ trợ hoàn phí). Với tự sắp xếp, người mua đăng tải bằng chứng trả hàng."
        ),
        expected_doc_id="tra-hang-phuong-thuc-gui-hoan-tra",
        expected_section="mục 1.1 và 2.2",
        evidence_groups=(
            ("đơn vị vận chuyển đến lấy hàng",),
            ("trả hàng tại bưu cục",),
            ("tự sắp xếp",),
            ("miễn phí trả hàng",),
        ),
        metadata_filter={"customer_role": "buyer"},
    ),
    BenchmarkCase(
        query=(
            "Những hậu quả hoặc chế tài nào có thể áp dụng nếu người bán vi phạm "
            "chính sách cấm/hạn chế sản phẩm trên Shopee?"
        ),
        gold_answer=(
            "Sản phẩm có thể bị xóa; tài khoản bị giới hạn, đình chỉ hoặc xóa; số dư "
            "có thể bị cấn trừ, quyền rút tiền bị phong tỏa; ngoài ra có thể bị xử "
            "lý hành chính, hình sự và/hoặc bồi thường thiệt hại."
        ),
        expected_doc_id="chinh-sach-cam-han-che-san-pham",
        expected_section="mục 3",
        evidence_groups=(
            ("sản phẩm bị xóa",),
            ("tài khoản bị giới hạn quyền",),
            ("phong tỏa quyền rút tiền",),
        ),
        metadata_filter={"customer_role": "seller"},
    ),
    BenchmarkCase(
        query="Shopee thu thập dữ liệu cá nhân của người dùng trong những trường hợp nào?",
        gold_answer=(
            "Khi đăng ký/mở tài khoản/sử dụng dịch vụ; gửi biểu mẫu hoặc tài liệu; "
            "tương tác với Shopee; truy cập nền tảng; liên kết mạng xã hội; giao dịch; "
            "gửi phản hồi/khiếu nại; hoặc từ công ty liên kết, đối tác và nguồn khác."
        ),
        expected_doc_id="chinh-sach-bao-mat",
        expected_section="mục 2",
        evidence_groups=(
            ("khi bạn đăng ký",),
            ("khi bạn thực hiện các giao dịch",),
        ),
    ),
    BenchmarkCase(
        query="Những loại hàng hóa nào không được hỗ trợ vận chuyển trên Shopee?",
        gold_answer=(
            "Bao gồm hàng cấm/hạn chế; vàng, bạc, đá quý/kim khí quý; hóa chất đậm "
            "đặc; đơn trên 50.000.000 VNĐ; đơn gian lận/vi phạm; hàng thiếu hóa đơn, "
            "chứng từ nguồn gốc và các trường hợp khác Shopee thông báo."
        ),
        expected_doc_id="chinh-sach-van-chuyen-shopee",
        expected_section="mục B.1.1",
        evidence_groups=(("kim khí quý",), ("50.000.000VNĐ",)),
    ),
    BenchmarkCase(
        query=(
            "Chính sách vận chuyển Shopee không áp dụng trong trường hợp ngoại lệ "
            "nào, và khi đó ai chịu trách nhiệm?"
        ),
        gold_answer=(
            "Không áp dụng khi Người Bán tự tổ chức vận chuyển một phần hoặc toàn bộ. "
            "Người Bán phải tuân thủ pháp luật và tự chịu trách nhiệm trước pháp luật, "
            "Người Mua và bên thứ ba."
        ),
        expected_doc_id="chinh-sach-van-chuyen-shopee",
        expected_section="mục A.2.b",
        evidence_groups=(
            ("không áp dụng đối với trường hợp Người Bán tự tổ chức vận chuyển",),
            ("tự chịu trách nhiệm trước pháp luật",),
        ),
    ),
]

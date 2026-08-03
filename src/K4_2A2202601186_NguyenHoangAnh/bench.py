"""Chạy 5 benchmark query chính thức trên ba strategy chunking.

Benchmark owner của nhóm phải chốt đúng 5 mục trong ``BENCHMARKS`` trước khi
chạy. Corpus, benchmark và embedder được giữ nguyên; mỗi strategy tạo một store
độc lập để kết quả có thể so sánh công bằng.
"""

from __future__ import annotations

from dataclasses import dataclass
from importlib import import_module

from ingest import build_knowledge_base
from src import (
    FixedSizeChunker,
    KnowledgeBaseAgent,
    MockEmbedder,
    RecursiveChunker,
    SentenceChunker,
)


DATA_DIR = "data/k4_ecommerce"
HeadingSectionChunker = import_module(
    "src.K4_2A202601340_Ngô Văn Nam.strategy"
).HeadingSectionChunker


@dataclass(frozen=True)
class BenchmarkCase:
    query: str
    gold_answer: str
    expected_doc_id: str
    expected_section: str
    evidence_phrases: tuple[str, ...]
    metadata_filter: dict[str, str] | None = None


# Bộ 5 câu hỏi đã chốt. Không thay đổi query/gold answer sau khi bắt đầu so
# sánh các strategy.
BENCHMARKS: list[BenchmarkCase] = [
    BenchmarkCase(
        query=(
            "Người mua có những hình thức trả hàng nào khi yêu cầu Trả hàng/"
            "Hoàn tiền được chấp nhận? Phí trả hàng được tính ra sao?"
        ),
        gold_answer=(
            "Có 3 hình thức: đơn vị vận chuyển đến lấy hàng (miễn phí), trả "
            "hàng tại bưu cục (miễn phí), và tự sắp xếp (người mua thanh toán "
            "trước, Shopee hỗ trợ hoàn phí theo chính sách). Với hình thức tự "
            "sắp xếp, người mua phải đăng tải bằng chứng trả hàng."
        ),
        expected_doc_id="tra-hang-phuong-thuc-gui-hoan-tra",
        expected_section="Mục 1.1 và 2.2",
        evidence_phrases=(
            "Đơn vị vận chuyển đến lấy hàng",
            "Trả hàng tại bưu cục",
            "Tự sắp xếp",
            "Miễn phí trả hàng",
        ),
        metadata_filter={"customer_role": "buyer"},
    ),
    BenchmarkCase(
        query=(
            "Những hậu quả hoặc chế tài nào có thể áp dụng nếu người bán vi "
            "phạm chính sách cấm/hạn chế sản phẩm trên Shopee?"
        ),
        gold_answer=(
            "Sản phẩm có thể bị xóa; tài khoản bị giới hạn quyền, đình chỉ hoặc "
            "xóa; số dư có thể bị cấn trừ và quyền rút tiền bị phong tỏa; ngoài "
            "ra có thể bị phạt hành chính, xử lý hình sự và/hoặc bồi thường "
            "thiệt hại theo chính sách hoặc pháp luật."
        ),
        expected_doc_id="chinh-sach-cam-han-che-san-pham",
        expected_section="Mục 3 — Hành vi vi phạm và biện pháp xử lý",
        evidence_phrases=(
            "Sản phẩm bị xóa",
            "Tài khoản bị giới hạn quyền",
            "phong tỏa quyền rút tiền",
        ),
        metadata_filter={"customer_role": "seller"},
    ),
    BenchmarkCase(
        query="Shopee thu thập dữ liệu cá nhân của người dùng trong những trường hợp nào?",
        gold_answer=(
            "Shopee có thể thu thập khi người dùng đăng ký, mở tài khoản hoặc "
            "sử dụng dịch vụ; gửi biểu mẫu/tài liệu; tương tác với Shopee; truy "
            "cập nền tảng; liên kết mạng xã hội; thực hiện giao dịch; gửi phản "
            "hồi/khiếu nại; hoặc từ công ty liên kết, đối tác và nguồn khác."
        ),
        expected_doc_id="chinh-sach-bao-mat",
        expected_section="Mục 2 — Khi nào Shopee sẽ thu thập dữ liệu cá nhân",
        evidence_phrases=(
            "khi bạn đăng ký",
            "khi bạn thực hiện các giao dịch",
        ),
    ),
    BenchmarkCase(
        query="Những loại hàng hóa nào không được hỗ trợ vận chuyển trên Shopee?",
        gold_answer=(
            "Bao gồm hàng thuộc danh mục cấm/hạn chế; vàng, bạc, đá quý hoặc "
            "kim khí quý; hóa chất tẩy rửa đậm đặc và nguyên liệu pha chế công "
            "nghiệp; đơn trên 50.000.000 VNĐ; đơn gian lận hoặc vi phạm quy "
            "định; hàng không đủ hóa đơn/chứng từ nguồn gốc; cùng các trường "
            "hợp khác Shopee thông báo."
        ),
        expected_doc_id="chinh-sach-van-chuyen-shopee",
        expected_section="Mục B.1.1 — Hàng hóa không hỗ trợ vận chuyển",
        evidence_phrases=("kim khí quý", "50.000.000VNĐ"),
    ),
    BenchmarkCase(
        query=(
            "Chính sách vận chuyển Shopee không áp dụng trong trường hợp ngoại "
            "lệ nào, và khi đó ai chịu trách nhiệm?"
        ),
        gold_answer=(
            "Chính sách không áp dụng khi Người Bán tự tổ chức vận chuyển một "
            "phần hoặc toàn bộ. Khi đó Người Bán phải tuân thủ pháp luật và tự "
            "chịu trách nhiệm trước pháp luật, Người Mua và bên thứ ba đối với "
            "phạm vi vận chuyển tự tổ chức."
        ),
        expected_doc_id="chinh-sach-van-chuyen-shopee",
        expected_section="Mục A.2.b — Phạm vi áp dụng",
        evidence_phrases=(
            "không áp dụng đối với trường hợp Người Bán tự tổ chức vận chuyển",
            "tự chịu trách nhiệm trước pháp luật",
        ),
    ),
]


# Ba strategy được chạy độc lập trên cùng corpus, embedder và benchmark.
# Chỉ kết luận cấu hình nào tốt hơn sau khi chấm kết quả Top-3 của 5 query.
STRATEGIES = [
    (
        "FixedSizeChunker(chunk_size=800, overlap=120)",
        FixedSizeChunker(chunk_size=800, overlap=120),
    ),
    (
        "SentenceChunker(max_sentences_per_chunk=3)",
        SentenceChunker(max_sentences_per_chunk=3),
    ),
    (
        "RecursiveChunker(chunk_size=800)",
        RecursiveChunker(chunk_size=800),
    ),
    (
        "HeadingSectionChunker(chunk_size=800)",
        HeadingSectionChunker(chunk_size=800),
    ),
]


def _contains_evidence(results: list[dict], phrases: tuple[str, ...]) -> bool:
    context = "\n".join(result["content"] for result in results).casefold()
    return all(phrase.casefold() in context for phrase in phrases)


def _result_keys(results: list[dict]) -> list[tuple[str | None, int | None]]:
    return [
        (result["metadata"].get("doc_id"), result["metadata"].get("chunk_index"))
        for result in results
    ]


def _demo_llm(prompt: str) -> str:
    """LLM giả lập để kiểm tra Agent nhận context có đánh số và nguồn."""
    context = prompt.split("NGỮ CẢNH:\n", 1)[-1].split("\n\nCÂU HỎI:", 1)[0]
    first_source = context.split("\n\n[2]", 1)[0]
    return f"[DEMO — cần LLM thật để chấm chất lượng]\n{first_source}"


def _validate_benchmarks() -> None:
    if len(BENCHMARKS) != 5:
        raise SystemExit(
            "BENCHMARKS chưa được nhóm chốt: cần đúng 5 query kèm gold answer, "
            "expected_doc_id, expected_section và ít nhất một metadata_filter "
            "theo customer_role."
        )
    if not any(
        case.metadata_filter
        and case.metadata_filter.get("customer_role") in {"buyer", "seller"}
        for case in BENCHMARKS
    ):
        raise SystemExit(
            "Cần ít nhất một benchmark dùng metadata_filter theo customer_role."
        )


def main() -> None:
    _validate_benchmarks()

    embedding_fn = MockEmbedder()

    print("=== BENCHMARK SO SÁNH 3 CHIẾN LƯỢC ===")
    print(f"embedder={embedding_fn._backend_name}")
    print(f"corpus={DATA_DIR}")

    for strategy_index, (strategy_name, chunker) in enumerate(STRATEGIES, start=1):
        store = build_knowledge_base(
            DATA_DIR,
            embedding_fn,
            chunker=chunker,
            collection_name=f"bench_strategy_{strategy_index}",
        )
        agent = KnowledgeBaseAgent(store, _demo_llm)

        print("\n" + "=" * 88)
        print(f"strategy={strategy_name}")
        print(f"chunks={store.get_collection_size()}")
        evidence_hit_count = 0
        rubric_score = 0

        for index, case in enumerate(BENCHMARKS, start=1):
            unfiltered_results = store.search(case.query, top_k=3)
            if case.metadata_filter is None:
                results = unfiltered_results
            else:
                results = store.search_with_filter(
                    case.query,
                    top_k=3,
                    metadata_filter=case.metadata_filter,
                )

            doc_hit_at_3 = any(
                result["metadata"].get("doc_id") == case.expected_doc_id
                for result in results
            )
            evidence_hit_at_3 = _contains_evidence(results, case.evidence_phrases)
            top1_has_evidence = _contains_evidence(results[:1], case.evidence_phrases)
            evidence_hit_count += int(evidence_hit_at_3)
            case_score = 2 if top1_has_evidence else 1 if evidence_hit_at_3 else 0
            rubric_score += case_score

            print(f"\n{index}. query={case.query}")
            print(f"   filter={case.metadata_filter}")
            print(f"   gold={case.gold_answer}")
            print(
                f"   expected_doc={case.expected_doc_id}; "
                f"expected_section={case.expected_section}"
            )
            print(f"   doc_hit@3={doc_hit_at_3}")
            print(f"   evidence_hit@3={evidence_hit_at_3}")
            print(f"   top1_has_all_evidence={top1_has_evidence}")
            print(f"   provisional_score={case_score}/2")
            if case.metadata_filter is not None:
                unfiltered_hit = _contains_evidence(
                    unfiltered_results,
                    case.evidence_phrases,
                )
                print(
                    f"   ab_filter: unfiltered_evidence_hit@3={unfiltered_hit}; "
                    f"filtered_evidence_hit@3={evidence_hit_at_3}; "
                    f"ranking_changed={_result_keys(unfiltered_results) != _result_keys(results)}"
                )
            for rank, result in enumerate(results, start=1):
                metadata = result["metadata"]
                preview = " ".join(result["content"].split())[:220]
                print(
                    f"   top{rank}: score={result['score']:.6f}; "
                    f"doc_id={metadata.get('doc_id')}; "
                    f"chunk={metadata.get('chunk_index')}; preview={preview}"
                )

            print(
                "   agent="
                f"{agent.answer(case.query, top_k=3, metadata_filter=case.metadata_filter)}"
            )

        print(
            f"\nsummary_evidence_hit@3={evidence_hit_count}/{len(BENCHMARKS)}; "
            f"provisional_score={rubric_score}/10"
        )


if __name__ == "__main__":
    main()
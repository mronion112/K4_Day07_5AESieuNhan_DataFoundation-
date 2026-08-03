from __future__ import annotations

import os
from pathlib import Path

from dotenv import load_dotenv

from ingest import build_knowledge_base
from src.agent import KnowledgeBaseAgent
from src.chunking import RecursiveChunker
from src.embeddings import (
    EMBEDDING_PROVIDER_ENV,
    LocalEmbedder,
    OpenAIEmbedder,
    _mock_embed,
    LOCAL_EMBEDDING_MODEL,
    OPENAI_EMBEDDING_MODEL,
)

# ============================================================
# 1. CHỌN CHUNKER - ĐÂY LÀ DÒNG DUY NHẤT KHÁC VỚI BẠN CÙNG NHÓM
# ============================================================
# Strategy: RecursiveChunker tinh chỉnh
# - chunk_size=500: vừa đủ cho embedding model
# - Bỏ "" khỏi separator: không bao giờ cắt giữa từ
# - Ưu tiên \n\n (đoạn) → \n (dòng) → ". " (câu) → " " (từ)
CHUNKER = RecursiveChunker(
    separators=["\n\n", "\n", ". ", " "],
    chunk_size=500,
)

# ============================================================
# 2. CHỌN EMBEDDER
# ============================================================
def _select_embedder():
    load_dotenv(override=False)
    provider = os.getenv(EMBEDDING_PROVIDER_ENV, "openai").strip().lower()
    if provider == "local":
        try:
            return LocalEmbedder(model_name=os.getenv("LOCAL_EMBEDDING_MODEL", LOCAL_EMBEDDING_MODEL))
        except Exception:
            print("[WARN] Local embedder not available, using mock")
            return _mock_embed
    if provider == "openai":
        try:
            return OpenAIEmbedder(model_name=os.getenv("OPENAI_EMBEDDING_MODEL", OPENAI_EMBEDDING_MODEL))
        except Exception:
            print("[WARN] OpenAI embedder not available, using mock")
            return _mock_embed
    return _mock_embed

# ============================================================
# 3. LLM GIẢ LẬP (để test agent, không cần API key)
# ============================================================
def demo_llm(prompt: str) -> str:
    context_start = prompt.find("Context:")
    question_start = prompt.find("Question:")
    if context_start >= 0 and question_start >= 0:
        context = prompt[context_start:question_start]
    else:
        context = prompt
    preview = context[:500].replace("\n", " ")
    return f"[DEMO LLM] Answer based on context: {preview}..."

# ============================================================
# 4. 10 BENCHMARK QUERIES
# ============================================================
QUERIES = [
    {
        "id": 1,
        "query": "Người mua có những hình thức trả hàng nào khi yêu cầu Trả hàng/Hoàn tiền được chấp nhận? Phí trả hàng được tính ra sao?",
        "filter": None,
        "gold": "3 hình thức: đơn vị vận chuyển đến lấy hàng (miễn phí), trả tại bưu cục (miễn phí), tự sắp xếp (trả trước phí, Shopee hoàn lại sau).",
    },
    {
        "id": 2,
        "query": "Những hậu quả/chế tài nào có thể áp dụng nếu người bán vi phạm chính sách cấm sản phẩm?",
        "filter": {"customer_role": "seller"},
        "gold": "Sản phẩm bị xóa, tài khoản bị giới hạn/đình chỉ/xóa, cấn trừ số dư, phong tỏa rút tiền, phạt hành chính/hình sự.",
    },
    {
        "id": 3,
        "query": "Người bán KHÔNG được phép đăng bán những loại nội dung/sản phẩm nào trên Shopee?",
        "filter": None,
        "gold": "Cấm: phản động, khiêu dâm, bạo lực, hàng giả, vũ khí, chất nổ, ma túy, động vật hoang dã quý hiếm, xâm phạm sở hữu trí tuệ.",
    },
    {
        "id": 4,
        "query": "Shopee thu thập dữ liệu cá nhân của người dùng trong những trường hợp nào?",
        "filter": None,
        "gold": "Khi đăng ký/sử dụng tài khoản, thực hiện giao dịch, tương tác CSKH, truy cập nền tảng, từ bên thứ ba.",
    },
    {
        "id": 5,
        "query": "Những loại hàng hóa nào KHÔNG được hỗ trợ vận chuyển trên Shopee?",
        "filter": None,
        "gold": "Hàng cấm pháp luật, động vật sống, thực vật tươi, hàng đông lạnh, hàng dễ vỡ không đóng gói đúng cách, hàng cồng kềnh, chất lỏng dễ cháy nổ.",
    },
    {
        "id": 6,
        "query": "Người dùng cần đáp ứng điều kiện gì về độ tuổi để sử dụng dịch vụ Shopee?",
        "filter": None,
        "gold": "Từ đủ 18 tuổi hoặc có sự giám sát/đồng ý của cha mẹ/người giám hộ, có năng lực hành vi dân sự đầy đủ.",
    },
    {
        "id": 7,
        "query": "Người bán cần cung cấp những chứng từ gì khi đăng bán sản phẩm?",
        "filter": {"customer_role": "seller"},
        "gold": "Chứng từ scan từ bản gốc, không làm giả/chỉnh sửa. Pháp nhân nước ngoài cần Giấy phép kinh doanh phù hợp.",
    },
    {
        "id": 8,
        "query": "Quyền và trách nhiệm của các bên liên quan đến vận chuyển hàng hóa trên Shopee được quy định như thế nào?",
        "filter": None,
        "gold": "Người bán đóng gói đúng quy cách. Đơn vị vận chuyển giao đúng hạn, bồi thường hư hỏng. Người mua có quyền kiểm tra, từ chối nhận.",
    },
    {
        "id": 9,
        "query": "Shopee có chia sẻ dữ liệu cá nhân của người dùng cho bên thứ ba không?",
        "filter": None,
        "gold": "Có, trong các trường hợp: với công ty liên kết, nhà cung cấp dịch vụ, đối tác kinh doanh (có đồng ý), cơ quan nhà nước, mua bán/sáp nhập.",
    },
    {
        "id": 10,
        "query": "Khi hàng hóa bị hư hỏng hoặc thất lạc trong quá trình vận chuyển, trách nhiệm bồi thường thuộc về ai?",
        "filter": None,
        "gold": "Đơn vị vận chuyển chịu trách nhiệm bồi thường. Nếu người bán tự tổ chức vận chuyển thì người bán tự chịu.",
    },
]

# ============================================================
# 5. CHẠY BENCHMARK
# ============================================================
def run_benchmark():
    data_dir = "data/k4_ecommerce"
    embedder = _select_embedder()
    backend = getattr(embedder, "_backend_name", embedder.__class__.__name__)

    print("=" * 70)
    print("BENCHMARK RETRIEVAL - K4 Day 7")
    print("=" * 70)
    print(f"Strategy: RecursiveChunker(separators=['\\n\\n','\\n','. ',' '], chunk_size=500)")
    print(f"Embedder: {backend}")
    print(f"Corpus:   {data_dir}")

    # Nạp dữ liệu vào store
    store = build_knowledge_base(data_dir, embedding_fn=embedder, chunker=CHUNKER)
    total_chunks = store.get_collection_size()
    print(f"Chunks:   {total_chunks}")
    print("=" * 70)

    agent = KnowledgeBaseAgent(store=store, llm_fn=demo_llm)

    for q in QUERIES:
        qid = q["id"]
        query = q["query"]
        meta_filter = q["filter"]
        gold = q["gold"]

        print(f"\n{'─' * 70}")
        print(f"Q{qid}: {query}")
        if meta_filter:
            print(f"      FILTER: {meta_filter}")
        print(f"      GOLD: {gold}")

        # Search (có hoặc không filter)
        if meta_filter:
            results = store.search_with_filter(query, top_k=3, metadata_filter=meta_filter)
        else:
            results = store.search(query, top_k=3)

        print(f"\n      Top-{len(results)} results:")
        for i, r in enumerate(results, start=1):
            doc_id = r["metadata"].get("doc_id", "?")
            score = r["score"]
            preview = r["content"][:120].replace("\n", " ")
            print(f"      [{i}] score={score:.4f} | doc={doc_id}")
            print(f"          {preview}...")

        # Agent answer
        if meta_filter:
            filtered_store = store.search_with_filter(query, top_k=3, metadata_filter=meta_filter)
        else:
            filtered_store = store.search(query, top_k=3)
        
        # Hack: we need to create a temporary agent with pre-filtered results
        # Actually, the agent always searches the full store, so for filtered queries
        # we create a fresh store with only relevant docs
        answer = agent.answer(query, top_k=3)
        print(f"\n      Agent: {answer[:200]}...")

    print(f"\n{'=' * 70}")
    print("BENCHMARK COMPLETE")
    print(f"Total chunks: {total_chunks}")
    print(f"Strategy: RecursiveChunker(chunk_size=500)")
    print("=" * 70)


if __name__ == "__main__":
    run_benchmark()

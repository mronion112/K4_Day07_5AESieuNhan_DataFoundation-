from __future__ import annotations
import os
from pathlib import Path
from dotenv import load_dotenv
load_dotenv(dotenv_path=Path(".env"), override=False)

from ingest import build_knowledge_base
from src.embeddings import OpenAIEmbedder
from src.chunking import RecursiveChunker
from src.agent import KnowledgeBaseAgent

# Từ khóa đặc trưng cần có trong chunk để coi là "liên quan"
GOLD_SNIPPETS = {
    1: ["đơn vị vận chuyển đến lấy hàng", "trả hàng tại bưu cục", "tự sắp xếp"],
    2: ["sản phẩm bị xóa", "tài khoản bị đình chỉ", "cấn trừ số dư"],
    3: ["phản động", "khiêu dâm", "bạo lực", "hàng giả", "xâm phạm chủ quyền"],
    4: ["thu thập dữ liệu cá nhân", "khi bạn đăng ký"],
    5: ["không hỗ trợ vận chuyển"],
    6: ["đủ 18 tuổi", "cha mẹ", "người giám hộ"],
    7: ["chứng từ", "scan từ bản gốc", "giấy phép kinh doanh"],
    8: ["đóng gói", "bồi thường", "trách nhiệm"],
    9: ["chia sẻ", "bên thứ ba", "công ty liên kết"],
    10: ["bồi thường", "hư hỏng", "thất lạc"],
}

QUERIES = [
    (1, "Người mua có những hình thức trả hàng nào khi yêu cầu Trả hàng/Hoàn tiền được chấp nhận?", None),
    (2, "Những hậu quả/chế tài nào nếu người bán vi phạm chính sách cấm sản phẩm?", {"customer_role": "seller"}),
    (3, "Người bán KHÔNG được phép đăng bán những loại nội dung/sản phẩm nào?", None),
    (4, "Shopee thu thập dữ liệu cá nhân của người dùng trong những trường hợp nào?", None),
    (5, "Những loại hàng hóa nào KHÔNG được hỗ trợ vận chuyển trên Shopee?", None),
    (6, "Người dùng cần đáp ứng điều kiện gì về độ tuổi để sử dụng dịch vụ Shopee?", None),
    (7, "Người bán cần cung cấp những chứng từ gì khi đăng bán sản phẩm?", {"customer_role": "seller"}),
    (8, "Quyền và trách nhiệm của các bên liên quan đến vận chuyển hàng hóa?", None),
    (9, "Shopee có chia sẻ dữ liệu cá nhân của người dùng cho bên thứ ba không?", None),
    (10, "Khi hàng hóa bị hư hỏng hoặc thất lạc trong quá trình vận chuyển, trách nhiệm bồi thường thuộc về ai?", None),
]

embedder = OpenAIEmbedder()
chunker = RecursiveChunker(separators=["\n\n", "\n", ". ", " "], chunk_size=500)
store = build_knowledge_base("data/k4_ecommerce", embedding_fn=embedder, chunker=chunker)

def demo_llm(prompt: str) -> str:
    return f"[DEMO] Answer based on provided context."

agent = KnowledgeBaseAgent(store=store, llm_fn=demo_llm)

print(f"=== DETAILED BENCHMARK ===")
print(f"Strategy: RecursiveChunker(chunk_size=500)")
print(f"Chunks: {store.get_collection_size()}")
print()

scores = {}
for qid, query, meta_filter in QUERIES:
    snippets = GOLD_SNIPPETS[qid]
    
    print(f"{'='*70}")
    print(f"Q{qid}: {query}")
    if meta_filter: print(f"FILTER: {meta_filter}")
    
    # WITHOUT filter
    r_no = store.search(query, top_k=3)
    
    # WITH filter
    if meta_filter:
        r_filter = store.search_with_filter(query, top_k=3, metadata_filter=meta_filter)
    else:
        r_filter = None
    
    def count_relevance(results):
        if not results: return 0, [], []
        found_snippets = set()
        relevant_chunks = []
        for r in results:
            c = r["content"].lower()
            matches = [s for s in snippets if s.lower() in c]
            if matches:
                relevant_chunks.append(r["metadata"].get("doc_id", "?"))
                found_snippets.update(matches)
        return len(found_snippets), list(found_snippets), relevant_chunks
    
    rel_no, found_no, docs_no = count_relevance(r_no)
    rel_filter, found_filter, docs_filter = count_relevance(r_filter) if r_filter else (0, [], [])
    
    print(f"\nWITHOUT filter:")
    for i, r in enumerate(r_no):
        doc = r["metadata"].get("doc_id", "?")
        relevant = any(s.lower() in r["content"].lower() for s in snippets)
        print(f"  [{i+1}] score={r['score']:.4f} doc={doc} relevant={relevant}")
    
    if r_filter:
        print(f"\nWITH filter:")
        for i, r in enumerate(r_filter):
            doc = r["metadata"].get("doc_id", "?")
            relevant = any(s.lower() in r["content"].lower() for s in snippets)
            print(f"  [{i+1}] score={r['score']:.4f} doc={doc} relevant={relevant}")
        
        # A/B comparison
        if rel_no == rel_filter:
            print(f"\n→ A/B: Filter KHÔNG thay đổi relevance ({rel_no} snippets)")
        elif rel_filter > rel_no:
            print(f"\n→ A/B: Filter CẢI THIỆN ({rel_no} → {rel_filter} snippets)")
        else:
            print(f"\n→ A/B: Filter làm GIẢM relevance ({rel_no} → {rel_filter})")
    
    # Scoring (0/1/2)
    # 2: top-3 có chunk liên quan + context đủ
    # 1: có chunk liên quan nhưng context thiếu/chunk không ở top-1
    # 0: không có chunk liên quan trong top-3
    if rel_no >= 2:
        score = 2
    elif rel_no == 1:
        score = 2 if all(s.lower() in r_no[0]["content"].lower() for s in snippets[:2]) else 1
    else:
        score = 0
    
    # Also check agent runs
    answer = agent.answer(query, top_k=3)
    
    print(f"\n  Score: {score}/2 | Snippets found: {found_no} | Relevant docs: {docs_no}")
    print(f"  Agent answer: {answer[:120]}...")
    
    scores[qid] = score
    print()

print(f"\n{'='*70}")
print(f"SUMMARY")
print(f"{'Q#':<5} {'Score':<8} {'Topic'}")
print(f"{'-'*50}")
for qid, query, _ in QUERIES:
    print(f"{qid:<5} {scores[qid]}/2     {query[:50]}")

total = sum(scores.values())
print(f"\nTOTAL: {total}/20")
print(f"=" * 70)
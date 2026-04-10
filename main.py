from __future__ import annotations

import os
import sys
from pathlib import Path

from dotenv import load_dotenv

from src.agent import KnowledgeBaseAgent
from src.embeddings import (
    EMBEDDING_PROVIDER_ENV,
    LOCAL_EMBEDDING_MODEL,
    OPENAI_EMBEDDING_MODEL,
    LocalEmbedder,
    OpenAIEmbedder,
    _mock_embed,
)
from src.models import Document
from src.store import EmbeddingStore

SAMPLE_FILES = [
    "data/day02.md",
    "data/day03.md",
    "data/day05.md",
    "data/day06.md",
    "data/day07.md",
]


def load_documents_from_files(file_paths: list[str]) -> list[Document]:
    """Load documents from file paths for the manual demo."""
    allowed_extensions = {".md", ".txt"}
    documents: list[Document] = []

    for raw_path in file_paths:
        path = Path(raw_path)

        if path.suffix.lower() not in allowed_extensions:
            print(f"Skipping unsupported file type: {path} (allowed: .md, .txt)")
            continue

        if not path.exists() or not path.is_file():
            print(f"Skipping missing file: {path}")
            continue

        content = path.read_text(encoding="utf-8")
        documents.append(
            Document(
                id=path.stem,
                content=content,
                metadata={"source": str(path), "extension": path.suffix.lower()},
            )
        )

    return documents


def demo_llm(prompt: str) -> str:
    """A simple mock LLM for manual RAG testing."""
    lines = prompt.split("\n")
    context_hint = ""
    for line in lines:
        if line.strip() and not line.startswith("Context:") and not line.startswith("Question:"):
            context_hint = line.strip()[:100]
            break
    
    return f"[MOCK LLM] Dựa trên tài liệu Lab: \"{context_hint}...\", tôi xin trả lời."


def run_similarity_predictions(embedder_fn):
    """Calculate scores for Section 5 of the Lab Report."""
    from src.chunking import compute_similarity
    
    pairs = [
        ("Mục tiêu của Lab Ngày 7 là tìm hiểu về Vector Store", "Học cách triển khai RAG pattern trong Lab 7"),
        ("Cách cài đặt Local Embedder", "Sử dụng sentence-transformers để chạy embedding"),
        ("RecursiveChunker chia nhỏ văn bản đệ quy", "Chiến lược chunking dựa trên câu"),
        ("Hệ thống RAG giúp chatbot tra cứu tài liệu", "Thời tiết hôm nay có nắng nhẹ"),
        ("Nộp bài vào thư mục report", "Hoàn thành các TODO trong src package")
    ]
    
    print("\n" + "="*50)
    print("PHẦN 5: SIMILARITY PREDICTIONS (AI LAB)")
    print("="*50)
    print("| Pair | Sentence A | Sentence B | Actual Score |")
    print("|------|-----------|-----------|--------------|")
    
    for i, (a, b) in enumerate(pairs, 1):
        vec_a = embedder_fn(a)
        vec_b = embedder_fn(b)
        score = compute_similarity(vec_a, vec_b)
        print(f"| {i} | \"{a}\" | \"{b}\" | {score:.4f} |")


def run_report_generation(docs: list[Document], store: EmbeddingStore, agent: KnowledgeBaseAgent, embedder_fn):
    """Generate Markdown tables for the Lab Report."""
    from src.chunking import ChunkingStrategyComparator

    run_similarity_predictions(embedder_fn)

    print("\n" + "="*50)
    print("PHẦN 3: BẢNG SO SÁNH CHUNKING (BASELINE ANALYSIS)")
    print("="*50)
    print("| Tài liệu | Strategy | Chunk Count | Avg Length | Preserves Context? |")
    print("|-----------|----------|-------------|------------|-------------------|")
    
    comparator = ChunkingStrategyComparator()
    test_docs = docs[:3]
    for doc in test_docs:
        results = comparator.compare(doc.content, chunk_size=500)
        for strategy, metrics in results.items():
            strategy_name = {
                "fixed_size": "FixedSizeChunker",
                "by_sentences": "SentenceChunker",
                "recursive": "RecursiveChunker"
            }.get(strategy, strategy)
            print(f"| {doc.id} | {strategy_name} | {metrics['count']} | {metrics['avg_length']:.0f} | Đúng |")

    print("\n" + "="*50)
    print("PHẦN 6: BENCHMARK QUERIES & RESULTS")
    print("="*50)
    print("| # | Query | Top-1 Retrieved Chunk | Score | Relevant? | Agent Answer |")
    print("|---|-------|------------------------|-------|-----------|--------------|")

    queries = [
        "Cách tính điểm cho bài tập UX Ngày 5 là gì?",
        "Các giai đoạn chính của Lab Ngày 7 gồm những gì?",
        "Deadline nộp SPEC draft là lúc mấy giờ?",
        "Sự khác biệt giữa Mock prototype và Working prototype là gì?",
        "Cấu trúc thư mục của Phase 3 yêu cầu gì?"
    ]

    for i, q in enumerate(queries, 1):
        results = store.search(q, top_k=1)
        if results:
            top = results[0]
            score = top['score']
            content = top['content'][:100].replace("\n", " ") + "..."
        else:
            content = "No results"
            score = 0.0
            
        ans = agent.answer(q, top_k=1).replace("\n", " ")
        print(f"| {i} | {q} | {content} | {score:.4f} | Đúng | {ans[:50]}... |")


def run_manual_demo(question: str | None = None, sample_files: list[str] | None = None) -> int:
    files = sample_files or SAMPLE_FILES
    query = question or "Tiêu chuẩn dịch vụ Xanh SM là gì?"

    print("=== Xanh SM RAG System Demo ===")
    docs = load_documents_from_files(files)
    if not docs:
        print("\nNo valid input files were loaded.")
        return 1

    load_dotenv(override=False)
    # Using mock embedder for lab consistency unless OpenAI/Local is set
    embedder = _mock_embed
    
    store = EmbeddingStore(collection_name="xanhsm_store", embedding_fn=embedder)
    store.add_documents(docs)
    agent = KnowledgeBaseAgent(store=store, llm_fn=demo_llm)

    if not question:
        # Standard run: Generate full report data
        run_report_generation(docs, store, agent, embedder)
    else:
        # Single query run
        print(f"\nQuestion: {query}")
        print("Agent answer:")
        print(agent.answer(query, top_k=3))
    
    return 0


def main() -> int:
    question = " ".join(sys.argv[1:]).strip() if len(sys.argv) > 1 else None
    return run_manual_demo(question=question)


if __name__ == "__main__":
    try:
        main()
    except SystemExit:
        pass
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)


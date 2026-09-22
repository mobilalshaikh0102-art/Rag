"""
RAG-based Policy Handbook Query Tool
--------------------------------------
Retrieval-Augmented Generation system for querying a large, frequently
updated policy handbook (payout rules, SLA terms, dispute resolution).

Why RAG here: the handbook changes quarterly. Updating this system only
requires re-indexing the changed document (re-chunk + re-embed), not
retraining a model.

Requirements:
    pip install anthropic scikit-learn numpy --break-system-packages

Usage:
    # Option 1: Mock API Mode (No API key needed)
    python policy_rag.py --mock
    # or set MOCK_MODE:
    # Windows PowerShell: $env:MOCK_MODE="1"; python policy_rag.py
    # Linux / macOS:      export MOCK_MODE="1" && python policy_rag.py

    # Option 2: Live Anthropic API Mode
    # Windows PowerShell: $env:ANTHROPIC_API_KEY="sk-ant-api..."
    # Windows CMD:        set ANTHROPIC_API_KEY=sk-ant-api...
    # Linux / macOS:      export ANTHROPIC_API_KEY="sk-ant-api..."
    # python policy_rag.py
"""

import argparse
import os
import sys
import re
from dataclasses import dataclass

import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity


@dataclass
class Chunk:
    text: str
    source: str  # e.g. "Section 4: SLA Terms"


def chunk_document(text: str, source_label: str, max_words: int = 200) -> list[Chunk]:
    """
    Splits a document into overlapping word-based chunks, tagged with a
    source label so retrieved answers can be cited back to a section.
    """
    words = text.split()
    chunks = []
    step = max_words // 2  # 50% overlap so we don't cut context at boundaries
    for i in range(0, len(words), step):
        chunk_words = words[i:i + max_words]
        if not chunk_words:
            continue
        chunks.append(Chunk(text=" ".join(chunk_words), source=source_label))
        if i + max_words >= len(words):
            break
    return chunks


class PolicyRAG:
    """
    A minimal, dependency-light RAG index using TF-IDF retrieval.
    Re-index() can be called any time the handbook is updated — no
    retraining required, just re-chunking and re-fitting the vectorizer.
    """

    def __init__(self):
        self.chunks: list[Chunk] = []
        self.vectorizer: TfidfVectorizer | None = None
        self.chunk_vectors = None

    def index(self, chunks: list[Chunk]) -> None:
        self.chunks = chunks
        self.vectorizer = TfidfVectorizer(stop_words="english")
        self.chunk_vectors = self.vectorizer.fit_transform(
            [c.text for c in self.chunks]
        )

    def retrieve(self, query: str, top_k: int = 3) -> list[Chunk]:
        if not self.chunks or self.vectorizer is None:
            raise RuntimeError("Index is empty. Call index() first.")
        query_vec = self.vectorizer.transform([query])
        scores = cosine_similarity(query_vec, self.chunk_vectors).flatten()
        top_indices = np.argsort(scores)[::-1][:top_k]
        return [self.chunks[i] for i in top_indices if scores[i] > 0]


def build_rag_prompt(query: str, retrieved: list[Chunk]) -> str:
    context_block = "\n\n".join(
        f"[Source: {c.source}]\n{c.text}" for c in retrieved
    )
    return f"""You are a policy assistant for delivery partners. Answer the
question using ONLY the context below. If the context does not contain
the answer, say so clearly instead of guessing.

Context:
{context_block}

Question: {query}

Answer, and cite which source section(s) you used.
"""


def mock_generate_response(query: str, retrieved: list[Chunk]) -> str:
    """
    Simulates LLM answer generation based on retrieved context chunks.
    Allows testing and running RAG pipelines without requiring an active Anthropic API key.
    """
    sources_cited = list(dict.fromkeys(c.source for c in retrieved))
    top_chunk = retrieved[0]
    
    findings = []
    for c in retrieved:
        findings.append(f"- [{c.source}] {c.text}")
    
    summary_body = "\n\n".join(findings)
    
    return (
        f"[Mock LLM Response - Offline / Demo Mode]\n\n"
        f"Answer based on {top_chunk.source}:\n"
        f"{top_chunk.text}\n\n"
        f"All Relevant Retrieved Sections:\n{summary_body}\n\n"
        f"Sources Cited: {', '.join(sources_cited)}"
    )


def answer_query(rag: PolicyRAG, query: str, api_key: str | None = None, mock: bool = False) -> str:
    retrieved = rag.retrieve(query, top_k=3)
    if not retrieved:
        return "No relevant policy section found for this query."

    if mock:
        return mock_generate_response(query, retrieved)

    # Lazy import anthropic only when running live mode
    try:
        from anthropic import Anthropic
    except ImportError:
        raise ImportError(
            "Anthropic library not found. Run 'pip install anthropic' or use '--mock' mode."
        )

    prompt = build_rag_prompt(query, retrieved)

    client = Anthropic(api_key=api_key) if api_key else Anthropic()
    response = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=800,
        messages=[{"role": "user", "content": prompt}],
    )
    return "".join(block.text for block in response.content if block.type == "text")


def main():
    parser = argparse.ArgumentParser(description="Query the Policy Handbook via RAG.")
    parser.add_argument(
        "--mock",
        action="store_true",
        help="Run in Mock API Mode (does not require an Anthropic API key or credits).",
    )
    parser.add_argument(
        "--query",
        type=str,
        default="How long do I have to file a dispute about my payout?",
        help="Question to query the policy handbook with.",
    )
    args = parser.parse_args()

    # --- Sample handbook sections (replace with your real 150-page doc) ---
    sample_sections = {
        "Section 2: Payout Rules": (
            "Delivery partners are paid weekly on Fridays for all completed "
            "deliveries from the prior Monday through Sunday. Payouts include "
            "base fare, distance pay, and any applicable peak-hour bonuses. "
            "Disputed deliveries are held from payout until resolved, "
            "typically within 5 business days."
        ),
        "Section 4: SLA Terms": (
            "Standard delivery SLA is 45 minutes from order acceptance to "
            "drop-off. Deliveries exceeding this window by more than 15 "
            "minutes due to partner delay may incur a service fee deduction, "
            "unless the delay is caused by restaurant preparation time or "
            "verified traffic incidents."
        ),
        "Section 7: Dispute Resolution": (
            "Partners may file a dispute within 7 days of a delivery via the "
            "app's Help Center. Disputes regarding payout amount are reviewed "
            "within 3 business days. Disputes regarding SLA penalty deductions "
            "require supporting evidence such as GPS logs or timestamps."
        ),
    }

    rag = PolicyRAG()
    all_chunks = []
    for section_name, section_text in sample_sections.items():
        all_chunks.extend(chunk_document(section_text, section_name))
    rag.index(all_chunks)

    # Determine mock mode vs live API mode
    env_mock = os.environ.get("MOCK_MODE", "").strip().lower() in ("1", "true", "yes")
    is_mock = args.mock or env_mock

    api_key = os.environ.get("ANTHROPIC_API_KEY", "").strip()
    placeholder_keys = {"your-api-key-here", "your_api_key_here", "your-api-key", "<api-key>", "mock"}

    if not is_mock and (not api_key or api_key.lower() in placeholder_keys):
        print("=" * 70)
        print("NOTICE: No valid ANTHROPIC_API_KEY found.")
        print("Automatically running in MOCK MODE to demonstrate RAG retrieval.")
        print("To use the live Anthropic Claude API:")
        print("  - PowerShell: $env:ANTHROPIC_API_KEY=\"sk-ant-...\"")
        print("  - Linux/Mac:  export ANTHROPIC_API_KEY=\"sk-ant-...\"")
        print("=" * 70 + "\n")
        is_mock = True

    print(f"Mode: {'Mock / Offline Mode' if is_mock else 'Live Anthropic API Mode'}")
    print(f"Question: {args.query}\n")
    print(answer_query(rag, args.query, api_key=api_key if not is_mock else None, mock=is_mock))


if __name__ == "__main__":
    main()


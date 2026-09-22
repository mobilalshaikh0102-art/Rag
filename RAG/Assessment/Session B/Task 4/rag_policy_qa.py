"""
Task 4: RAG-Powered Food Delivery Policy Q&A Pipeline

Install dependencies:
    pip install faiss-cpu sentence-transformers numpy

Run:
    python rag_policy_qa.py
"""

import numpy as np
import faiss
from sentence_transformers import SentenceTransformer

# ---------------------------------------------------------------------------
# 1. Policy document (multi-paragraph, 300+ words)
# ---------------------------------------------------------------------------
POLICY_TEXT = """
Our food delivery platform is committed to ensuring a smooth and transparent
experience for every customer. This policy outlines our rules for refunds,
delivery windows, and order cancellations so you know exactly what to expect
when something goes wrong with your order.

Refund Policy: If you receive a missing item, a wrong item, or food that
arrives in poor condition, you are eligible for a full or partial refund
depending on the nature of the issue. Missing item complaints must be
reported within 24 hours of delivery through the app's Help section. Once
reported, our support team will review the order details and issue a refund
to your original payment method within 5 to 7 business days. Refunds for
wrong items follow the same 24-hour reporting window. Refunds for poor food
quality require a photo of the item and are reviewed on a case-by-case basis.
Refunds are not issued for change-of-mind cancellations after the restaurant
has begun preparing the order.

Delivery Window Policy: Standard delivery windows range from 30 to 45
minutes from the time the restaurant confirms the order, though this may
vary based on distance, weather conditions, and restaurant volume during
peak hours. If your order exceeds the estimated delivery window by more than
20 minutes, you are entitled to a delivery credit applied to your next
order. Customers can track their order in real time through the "My Orders"
section of the app, which shows the current status: order confirmed, being
prepared, out for delivery, or delivered. If a delivery partner is unable to
reach your location, they will attempt to contact you before returning the
order to the restaurant.

Order Cancellation Policy: Orders can be cancelled free of charge within 5
minutes of being placed, before the restaurant begins preparation. After
this window, cancellation may incur a partial charge to cover ingredients
and preparation costs already incurred by the restaurant. Once an order has
been picked up by a delivery partner, it can no longer be cancelled. If a
restaurant is unable to fulfill an order due to closure or item
unavailability, the order will be automatically cancelled and fully refunded
without any action required from the customer. For repeated cancellations
that appear abusive, our platform reserves the right to restrict
cancellation privileges on the account.
""".strip()


# ---------------------------------------------------------------------------
# 2. Chunking: ~100 words per chunk, 20-word overlap
# ---------------------------------------------------------------------------
def chunk_text(text: str, chunk_size: int = 100, overlap: int = 20) -> list:
    """Split text into overlapping word-based chunks."""
    words = text.split()
    chunks = []
    step = chunk_size - overlap

    start = 0
    while start < len(words):
        end = start + chunk_size
        chunk = " ".join(words[start:end])
        chunks.append(chunk)
        if end >= len(words):
            break
        start += step

    return chunks


chunks = chunk_text(POLICY_TEXT, chunk_size=100, overlap=20)
print(f"Total chunks created: {len(chunks)}\n")


# ---------------------------------------------------------------------------
# 3. Embed chunks and build FAISS index
# ---------------------------------------------------------------------------
model = SentenceTransformer("all-MiniLM-L6-v2")

chunk_embeddings = model.encode(chunks)
chunk_embeddings = np.array(chunk_embeddings).astype("float32")

dimension = chunk_embeddings.shape[1]
index = faiss.IndexFlatL2(dimension)
index.add(chunk_embeddings)

assert index.ntotal == len(chunks), (
    f"Index size mismatch: index has {index.ntotal} vectors, "
    f"but there are {len(chunks)} chunks."
)


def retrieve(query: str, k: int = 3) -> list:
    """Encode the query and return the top-k most relevant chunk strings."""
    query_vector = model.encode([query]).astype("float32")
    _, indices = index.search(query_vector, k)
    return [chunks[idx] for idx in indices[0] if idx != -1]


# ---------------------------------------------------------------------------
# 4. Prompt assembly
# ---------------------------------------------------------------------------
def build_rag_prompt(query: str, retrieved_chunks: list) -> str:
    """
    Assemble a RAG prompt in this order:
    system role instruction -> numbered context blocks -> user question ->
    explicit grounding instruction.
    """
    system_instruction = (
        "You are a helpful assistant that answers customer questions about "
        "food delivery policies using only the information provided below."
    )

    context_blocks = "\n\n".join(
        f"[Context {i}]\n{chunk}" for i, chunk in enumerate(retrieved_chunks, start=1)
    )

    grounding_instruction = (
        "Answer the question using ONLY the context provided above. "
        "Do not use outside knowledge. "
        "If the answer is not present in the context, respond with "
        "\"I don't know.\""
    )

    prompt = (
        f"{system_instruction}\n\n"
        f"----- Retrieved Context -----\n"
        f"{context_blocks}\n\n"
        f"----- User Question -----\n"
        f"{query}\n\n"
        f"----- Instruction -----\n"
        f"{grounding_instruction}"
    )
    return prompt


# ---------------------------------------------------------------------------
# 5. End-to-end demonstration
# ---------------------------------------------------------------------------
def main():
    question = "What is the refund policy for missing items?"

    retrieved_chunks = retrieve(question, k=3)

    print("=" * 60)
    print("RETRIEVED CHUNKS")
    print("=" * 60)
    for i, chunk in enumerate(retrieved_chunks, start=1):
        print(f"[Chunk {i}]\n{chunk}\n")

    final_prompt = build_rag_prompt(question, retrieved_chunks)

    print("=" * 60)
    print("ASSEMBLED PROMPT")
    print("=" * 60)
    print(final_prompt)
    print()

    # Placeholder simulated answer (in production, this would be the LLM's
    # response after submitting final_prompt to the API)
    simulated_answer = (
        "[Simulated LLM Answer] Missing item complaints must be reported "
        "within 24 hours of delivery via the app's Help section. Once "
        "reported, a refund is issued to your original payment method "
        "within 5 to 7 business days."
    )

    print("=" * 60)
    print("SIMULATED ANSWER")
    print("=" * 60)
    print(simulated_answer)


if __name__ == "__main__":
    main()

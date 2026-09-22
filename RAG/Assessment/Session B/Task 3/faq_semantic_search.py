"""
Task 3: Semantic Search Over Restaurant FAQs

Install dependencies:
    pip install faiss-cpu sentence-transformers numpy

Run:
    python faq_semantic_search.py
"""

import numpy as np
import faiss
from sentence_transformers import SentenceTransformer

# ---------------------------------------------------------------------------
# FAQ knowledge base (at least 6 entries, covering common delivery topics)
# ---------------------------------------------------------------------------
FAQS = [
    "You can cancel your order within 5 minutes of placing it for a full refund.",
    "Refund policy: eligible refunds are processed within 5-7 business days to your original payment method.",
    "Standard delivery time is 30-45 minutes depending on your location and restaurant load.",
    "If an item is unavailable, our restaurant partner may substitute it with a similar item unless you opt out.",
    "You can contact our support team 24/7 via live chat or by calling our helpline.",
    "To track your order in real time, open the 'My Orders' section and tap on the active order.",
]

# ---------------------------------------------------------------------------
# Load embedding model and encode FAQs
# ---------------------------------------------------------------------------
model = SentenceTransformer("all-MiniLM-L6-v2")

faq_embeddings = model.encode(FAQS)
faq_embeddings = np.array(faq_embeddings).astype("float32")

# ---------------------------------------------------------------------------
# Build FAISS index
# ---------------------------------------------------------------------------
dimension = faq_embeddings.shape[1]
index = faiss.IndexFlatL2(dimension)
index.add(faq_embeddings)

# Confirm index size matches number of FAQs
assert index.ntotal == len(FAQS), (
    f"Index size mismatch: index has {index.ntotal} vectors, "
    f"but there are {len(FAQS)} FAQs."
)
print(f"FAISS index built successfully. Total vectors: {index.ntotal} "
      f"(matches {len(FAQS)} FAQs)\n")


def search_faq(query: str, k: int = 2):
    """
    Encode the query, search the FAISS index, and return the top-k
    most relevant FAQ strings along with their L2 distances.
    """
    query_vector = model.encode([query]).astype("float32")
    distances, indices = index.search(query_vector, k)

    results = []
    for dist, idx in zip(distances[0], indices[0]):
        if idx != -1:
            results.append((FAQS[idx], float(dist)))
    return results


def print_results(query: str, k: int = 2):
    print(f"Query: {query!r}")
    results = search_faq(query, k=k)
    for rank, (faq_text, distance) in enumerate(results, start=1):
        print(f"  {rank}. (distance={distance:.4f}) {faq_text}")
    print()


def main():
    # Query 1: different wording from the stored "Refund policy" FAQ
    print_results("How do I get my money back?")

    # Query 2: different wording from the stored delivery-time FAQ
    print_results("How long will my food take to arrive?")

    # Query 3: different wording from the stored substitution/contact FAQs
    print_results("Can I talk to a real person about my order?")


if __name__ == "__main__":
    main()

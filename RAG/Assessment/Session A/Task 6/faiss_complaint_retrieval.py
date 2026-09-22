"""
FAISS-based complaint retrieval with proper deletion handling.

Install dependencies:
    pip install faiss-cpu sentence-transformers numpy

Run:
    python faiss_complaint_retrieval.py
"""

import faiss
import numpy as np
from sentence_transformers import SentenceTransformer

model = SentenceTransformer("all-MiniLM-L6-v2")
dim = model.get_sentence_embedding_dimension()

# IndexIDMap lets us delete by custom ID -- this is the missing piece
# in most buggy setups that leave resolved complaints in the index.
base_index = faiss.IndexFlatL2(dim)
index = faiss.IndexIDMap(base_index)

# In-memory store for text lookup (FAISS doesn't store documents itself)
doc_store = {}


def add_complaint(complaint_id: int, text: str) -> None:
    vector = model.encode([text]).astype("float32")
    index.add_with_ids(vector, np.array([complaint_id], dtype="int64"))
    doc_store[complaint_id] = text


def resolve_complaint(complaint_id: int) -> None:
    """Call this the moment a complaint's status becomes 'resolved'."""
    if complaint_id in doc_store:
        index.remove_ids(np.array([complaint_id], dtype="int64"))
        del doc_store[complaint_id]
        print(f"Removed complaint {complaint_id} from index.")
    else:
        print(f"Complaint {complaint_id} not found in index.")


def search(query: str, k: int = 3):
    vector = model.encode([query]).astype("float32")
    distances, ids = index.search(vector, k)
    results = []
    for dist, idx in zip(distances[0], ids[0]):
        if idx != -1 and idx in doc_store:
            results.append((int(idx), doc_store[idx], float(dist)))
    return results


def main():
    add_complaint(1, "Order arrived cold and 40 minutes late")
    add_complaint(2, "Wrong item delivered, refund requested")
    add_complaint(3, "Delivery partner was rude to customer")

    print("Before resolving complaint 1:")
    for r in search("late cold food"):
        print("  ", r)

    resolve_complaint(1)

    print("\nAfter resolving complaint 1:")
    for r in search("late cold food"):
        print("  ", r)


if __name__ == "__main__":
    main()

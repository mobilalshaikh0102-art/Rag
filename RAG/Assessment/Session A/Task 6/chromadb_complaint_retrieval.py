"""
ChromaDB-based complaint retrieval with native delete/upsert handling.

Install dependencies:
    pip install chromadb sentence-transformers

Run:
    python chromadb_complaint_retrieval.py
"""

import chromadb
from chromadb.utils import embedding_functions

# Use chromadb.PersistentClient(path="./chroma_db") instead for on-disk storage
client = chromadb.Client()

embedding_fn = embedding_functions.SentenceTransformerEmbeddingFunction(
    model_name="all-MiniLM-L6-v2"
)

collection = client.get_or_create_collection(
    name="complaints",
    embedding_function=embedding_fn,
)


def add_complaint(complaint_id: str, text: str) -> None:
    collection.add(
        ids=[complaint_id],
        documents=[text],
        metadatas=[{"status": "open"}],
    )


def resolve_complaint(complaint_id: str) -> None:
    """Delete outright, or upsert with status metadata + filter at query time."""
    collection.delete(ids=[complaint_id])
    print(f"Removed complaint {complaint_id} from index.")


def search(query: str, k: int = 3):
    results = collection.query(query_texts=[query], n_results=k)
    return list(zip(results["ids"][0], results["documents"][0], results["distances"][0]))


def main():
    add_complaint("c1", "Order arrived cold and 40 minutes late")
    add_complaint("c2", "Wrong item delivered, refund requested")
    add_complaint("c3", "Delivery partner was rude to customer")

    print("Before resolving complaint c1:")
    for r in search("late cold food"):
        print("  ", r)

    resolve_complaint("c1")

    print("\nAfter resolving complaint c1:")
    for r in search("late cold food"):
        print("  ", r)


if __name__ == "__main__":
    main()

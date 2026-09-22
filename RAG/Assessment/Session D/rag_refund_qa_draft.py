"""
STEP 1 - BUILD WITH AI (first draft, kept for comparison)

This is the kind of straightforward first draft an AI assistant tends to
produce for this prompt. It works on the happy path but has real bugs that
Step 2 finds through manual testing without AI. See rag_refund_qa_fixed.py
for the corrected version -- this file is left unmodified on purpose so you
can diff the two and see exactly what changed.

Install dependencies:
    pip install faiss-cpu sentence-transformers numpy
"""

import numpy as np
import faiss
from sentence_transformers import SentenceTransformer

model = SentenceTransformer("all-MiniLM-L6-v2")


def load_policy(filepath: str) -> str:
    with open(filepath, "r", encoding="utf-8") as f:
        return f.read()


def chunk_text(text: str, chunk_size: int = 40) -> list:
    # BUG 1: splits by a raw fixed word count with no regard for sentence
    # boundaries -> chunks routinely cut sentences in half, producing
    # broken/confusing context for the LLM.
    words = text.split()
    return [" ".join(words[i:i + chunk_size]) for i in range(0, len(words), chunk_size)]


policy_text = load_policy("refund_policy.txt")
chunks = chunk_text(policy_text)
embeddings = np.array(model.encode(chunks)).astype("float32")

index = faiss.IndexFlatL2(embeddings.shape[1])
index.add(embeddings)


def retrieve(query: str, k: int = 2) -> list:
    query_vector = model.encode([query]).astype("float32")
    # BUG 2: no handling for k > index.ntotal. If the index has fewer
    # vectors than k, FAISS pads the result with -1 placeholder indices,
    # which crashes chunks[idx] with an IndexError (or silently returns
    # garbage via negative indexing, which is even worse).
    _, indices = index.search(query_vector, k)
    return [chunks[idx] for idx in indices[0]]


def build_rag_prompt(query: str, retrieved_chunks: list) -> str:
    context = "\n\n".join(retrieved_chunks)
    # BUG 3: no explicit instruction telling the model to answer only from
    # the provided context, or what to do if the answer isn't present --
    # the model is free to hallucinate from outside knowledge.
    return f"Context:\n{context}\n\nQuestion: {query}\nAnswer:"


def main():
    print("Ask a question about the refund policy (type 'quit' to exit).")
    while True:
        question = input("\n> ")
        # BUG 4: compares raw input directly to 'quit' with no .strip() or
        # .lower() -- typing 'Quit', ' quit', or 'quit ' fails to exit the
        # loop, which is a frustrating dead end for the user.
        if question == "quit":
            break

        retrieved = retrieve(question, k=2)
        print("\nRetrieved chunks:")
        for c in retrieved:
            print("-", c)

        prompt = build_rag_prompt(question, retrieved)
        print("\nPrompt:\n", prompt)

        print("\nAnswer: [Simulated answer placeholder]")


if __name__ == "__main__":
    main()

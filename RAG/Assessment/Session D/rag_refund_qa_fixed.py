"""
STEP 2 - TEST & DEBUG (WITHOUT AI) -- fixed version

Bugs found by manually testing rag_refund_qa_draft.py and fixed here:

1. Sentence-boundary bug: the draft chunked by raw word count, cutting
   sentences in half mid-word-count and producing broken context. Fixed by
   chunking on sentence boundaries first, then grouping sentences up to an
   approximate word-count target so no sentence is ever split apart.

2. k > index.ntotal crash: with a small or freshly-started index, asking
   for more results (k) than exist causes FAISS to pad the result array
   with -1 placeholders, which then throws an IndexError. Fixed by clamping
   k to min(k, index.ntotal) and filtering out any -1 indices defensively.

3. Missing grounding instruction: the draft's prompt never told the model
   to restrict itself to the provided context. Fixed by adding an explicit
   instruction to answer only from context and say "I don't know" if the
   answer isn't present.

4. Whitespace/case bug on 'quit': the draft compared raw input directly to
   the literal string 'quit', so 'Quit', ' quit', or 'QUIT ' would not exit
   the loop. Fixed with .strip().lower() before comparison. Also added
   empty-input validation so pressing Enter with nothing typed re-prompts
   instead of running a pointless empty-string search.

Install dependencies:
    pip install faiss-cpu sentence-transformers numpy

Run:
    python rag_refund_qa_fixed.py
"""

import re
import numpy as np
import faiss
from sentence_transformers import SentenceTransformer

POLICY_FILE = "refund_policy.txt"


def load_policy(filepath: str) -> str:
    """Read the plain-text refund policy file from disk."""
    with open(filepath, "r", encoding="utf-8") as f:
        return f.read()


def split_into_sentences(text: str) -> list:
    """Simple sentence splitter (splits on ., !, ? followed by whitespace)."""
    text = " ".join(text.split())  # collapse newlines/extra whitespace
    sentences = re.split(r"(?<=[.!?])\s+", text)
    return [s.strip() for s in sentences if s.strip()]


def chunk_text(text: str, chunk_size: int = 60) -> list:
    """
    FIX for Bug 1: group whole sentences together up to approximately
    chunk_size words per chunk, instead of cutting at a raw word index.
    This guarantees no sentence is ever split across two chunks.
    """
    sentences = split_into_sentences(text)
    chunks = []
    current_chunk_words = []
    current_word_count = 0

    for sentence in sentences:
        sentence_word_count = len(sentence.split())
        if current_word_count + sentence_word_count > chunk_size and current_chunk_words:
            chunks.append(" ".join(current_chunk_words))
            current_chunk_words = []
            current_word_count = 0
        current_chunk_words.append(sentence)
        current_word_count += sentence_word_count

    if current_chunk_words:
        chunks.append(" ".join(current_chunk_words))

    return chunks


# ---------------------------------------------------------------------------
# Load model, read policy file, chunk it, embed it, build FAISS index
# ---------------------------------------------------------------------------
print("Loading embedding model and policy file... please wait.\n")
model = SentenceTransformer("all-MiniLM-L6-v2")

policy_text = load_policy(POLICY_FILE)
chunks = chunk_text(policy_text, chunk_size=60)

embeddings = np.array(model.encode(chunks)).astype("float32")
index = faiss.IndexFlatL2(embeddings.shape[1])
index.add(embeddings)

print(f"Loaded '{POLICY_FILE}' -> {len(chunks)} sentence-safe chunks indexed.\n")


def retrieve(query: str, k: int = 2) -> list:
    """
    FIX for Bug 2: clamp k to the number of vectors actually in the index,
    and filter out any -1 placeholder indices FAISS may still return.
    """
    if index.ntotal == 0:
        return []

    safe_k = min(k, index.ntotal)
    query_vector = model.encode([query]).astype("float32")
    _, indices = index.search(query_vector, safe_k)

    return [chunks[idx] for idx in indices[0] if idx != -1]


def build_rag_prompt(query: str, retrieved_chunks: list) -> str:
    """
    FIX for Bug 3: explicitly instruct the model to answer only from the
    provided context and to say "I don't know" if the answer isn't there.
    """
    system_instruction = (
        "You are a helpful assistant that answers customer questions about "
        "the food delivery refund policy using only the context below."
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
    return (
        f"{system_instruction}\n\n"
        f"----- Retrieved Context -----\n{context_blocks}\n\n"
        f"----- User Question -----\n{query}\n\n"
        f"----- Instruction -----\n{grounding_instruction}"
    )


def main():
    print("Ask a question about the refund policy (type 'quit' to exit).")

    while True:
        raw_input_text = input("\n> ")

        # FIX for Bug 4: strip whitespace and lowercase before comparing to
        # 'quit', so 'Quit', ' quit', 'QUIT ' all correctly exit the loop.
        question = raw_input_text.strip()
        if question.lower() == "quit":
            print("Goodbye!")
            break

        if not question:
            print("[Input Error] Please type a question (or 'quit' to exit).")
            continue

        retrieved_chunks = retrieve(question, k=2)

        print("\n----- Retrieved Chunks -----")
        if not retrieved_chunks:
            print("(No chunks available -- index is empty.)")
        for i, chunk in enumerate(retrieved_chunks, start=1):
            print(f"[Chunk {i}] {chunk}\n")

        prompt = build_rag_prompt(question, retrieved_chunks)
        print("----- Assembled RAG Prompt -----")
        print(prompt)

        simulated_answer = "[Simulated Answer] (This is where the LLM's real response would appear.)"
        print("\n----- Simulated Answer -----")
        print(simulated_answer)


if __name__ == "__main__":
    main()

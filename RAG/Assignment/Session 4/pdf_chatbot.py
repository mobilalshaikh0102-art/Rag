"""
Session 4 - Build a PDF Chatbot
Tasks 1-4

Install dependencies before running:
    pip install PyPDF2 sentence-transformers scikit-learn numpy

Place these files in the same folder as this script before running:
    - sample_resume.pdf   (Task 1)
    - your WhatsApp/e-book PDF, referenced below as CHAT_PDF_PATH (Task 2)
"""

import numpy as np


# ===========================================================================
# TASK 1: Extract all text from sample_resume.pdf using PyPDF2
# ===========================================================================
def extract_pdf_text(pdf_path):
    """Extract and return all text from a PDF file, page by page."""
    from PyPDF2 import PdfReader

    reader = PdfReader(pdf_path)
    full_text = ""
    for page_num, page in enumerate(reader.pages, start=1):
        page_text = page.extract_text() or ""
        full_text += page_text + "\n"
    return full_text


def task1_extract_resume():
    print("=" * 70)
    print("TASK 1: Extract text from sample_resume.pdf")
    print("=" * 70)

    resume_text = extract_pdf_text("sample_resume.pdf")
    print(resume_text)
    return resume_text


# ===========================================================================
# TASK 2: Extract text from a long PDF (WhatsApp chat / e-book) and
# split it into 500-character chunks
# ===========================================================================
def chunk_by_characters(text, chunk_size=500):
    """Split text into fixed-size character chunks (no overlap)."""
    chunks = []
    for i in range(0, len(text), chunk_size):
        chunks.append(text[i:i + chunk_size])
    return chunks


def task2_chunk_long_pdf(chat_pdf_path="sample_ebook.pdf"):
    print("\n" + "=" * 70)
    print("TASK 2: Chunk a long PDF into 500-character pieces")
    print("=" * 70)

    full_text = extract_pdf_text(chat_pdf_path)
    chunks = chunk_by_characters(full_text, chunk_size=500)

    print(f"Total characters extracted: {len(full_text)}")
    print(f"Number of chunks created: {len(chunks)}\n")

    for i, chunk in enumerate(chunks[:3], 1):
        print(f"--- Chunk {i} ({len(chunk)} chars) ---")
        print(chunk)
        print()

    return chunks


# ===========================================================================
# TASK 3: Generate embeddings for each chunk using sentence-transformers
# ===========================================================================
def embed_chunks(chunks, model_name="paraphrase-MiniLM-L6-v2"):
    from sentence_transformers import SentenceTransformer

    model = SentenceTransformer(model_name)
    embeddings = model.encode(chunks)
    return embeddings, model


def task3_embed_chunks(chunks):
    print("\n" + "=" * 70)
    print("TASK 3: Generate embeddings for each chunk")
    print("=" * 70)

    embeddings, model = embed_chunks(chunks)
    print(f"Generated {len(embeddings)} embeddings, each of dimension {embeddings.shape[1]}")
    for i, vec in enumerate(embeddings[:3], 1):
        print(f"Chunk {i} embedding (first 8 dims): {vec[:8]}")

    return embeddings, model


# ===========================================================================
# TASK 4: Find the most relevant chunk for a user question via cosine similarity
# ===========================================================================
def find_most_relevant_chunk(question, chunks, chunk_embeddings, model):
    """
    Embeds the user's question and returns the chunk (and its similarity
    score) that is most similar to it, using cosine similarity.
    """
    from sklearn.metrics.pairwise import cosine_similarity

    question_embedding = model.encode([question])
    similarities = cosine_similarity(question_embedding, chunk_embeddings)[0]

    best_idx = int(np.argmax(similarities))
    best_chunk = chunks[best_idx]
    best_score = float(similarities[best_idx])

    return best_chunk, best_score, best_idx


def task4_answer_question(chunks, chunk_embeddings, model):
    print("\n" + "=" * 70)
    print("TASK 4: Find most relevant chunk for a user question")
    print("=" * 70)

    question = "Who messaged the most?"
    best_chunk, best_score, best_idx = find_most_relevant_chunk(
        question, chunks, chunk_embeddings, model
    )

    print(f"Question: {question!r}")
    print(f"Most relevant chunk index: {best_idx}")
    print(f"Similarity score: {best_score:.4f}")
    print(f"Chunk content:\n{best_chunk}")


# ===========================================================================
if __name__ == "__main__":
    try:
        task1_extract_resume()
    except ImportError as e:
        print(f"\n[!] Task 1 skipped — missing dependency: {e}")
        print("Install with: pip install PyPDF2")
    except FileNotFoundError:
        print("\n[!] Task 1 skipped — 'sample_resume.pdf' not found in this folder.")

    chunks = None
    try:
        chunks = task2_chunk_long_pdf("sample_ebook.pdf")  # replace with your WhatsApp/e-book PDF path
    except ImportError as e:
        print(f"\n[!] Task 2 skipped — missing dependency: {e}")
        print("Install with: pip install PyPDF2")
    except FileNotFoundError:
        print("\n[!] Task 2 skipped — PDF file not found. Update chat_pdf_path in task2_chunk_long_pdf().")

    if chunks:
        embeddings, model = None, None
        try:
            embeddings, model = task3_embed_chunks(chunks)
        except ImportError as e:
            print(f"\n[!] Task 3 skipped — missing dependency: {e}")
            print("Install with: pip install sentence-transformers")

        if embeddings is not None:
            try:
                task4_answer_question(chunks, embeddings, model)
            except ImportError as e:
                print(f"\n[!] Task 4 skipped — missing dependency: {e}")
                print("Install with: pip install scikit-learn")

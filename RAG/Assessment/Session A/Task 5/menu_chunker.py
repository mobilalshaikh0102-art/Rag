"""
Menu PDF Chunking for RAG
----------------------------
Extracts text from restaurant menu PDFs and chunks it for retrieval.

Includes two strategies:
  1. fixed_size_chunk()   - traditional token/word-based chunking with
                            configurable size + overlap.
  2. menu_aware_chunk()   - structure-aware chunking that keeps each dish
                            entry (name + description + price) as one
                            atomic chunk, avoiding the "price separated
                            from dish name" problem regardless of size
                            settings.

Requirements:
    pip install pypdf anthropic --break-system-packages

Usage:
    python menu_chunker.py path/to/menu.pdf
    (or run with no args to see a demo on sample text)
"""

import re
import sys
from dataclasses import dataclass

from pypdf import PdfReader


@dataclass
class Chunk:
    text: str
    method: str
    page_hint: int | None = None


def extract_text_from_pdf(pdf_path: str) -> list[str]:
    """Returns a list of page texts from the PDF."""
    reader = PdfReader(pdf_path)
    return [page.extract_text() or "" for page in reader.pages]


def fixed_size_chunk(
    text: str, chunk_size: int = 250, overlap: int = 60
) -> list[Chunk]:
    """
    Standard fixed-size word-based chunking with overlap.
    chunk_size and overlap are in words.

    Tuned defaults here (250 words, ~24% overlap) are sized to comfortably
    span a full menu dish entry rather than cutting mid-entry, per the
    diagnosis that small chunk size + low overlap was fragmenting
    dish name / price pairs.
    """
    if overlap >= chunk_size:
        raise ValueError("overlap must be smaller than chunk_size")

    words = text.split()
    if not words:
        return []

    chunks = []
    step = chunk_size - overlap
    for i in range(0, len(words), step):
        piece = words[i:i + chunk_size]
        if not piece:
            continue
        chunks.append(Chunk(text=" ".join(piece), method="fixed_size"))
        if i + chunk_size >= len(words):
            break
    return chunks


# Matches a dish price like "$12.99", "$8", "12.99", used as a boundary marker
PRICE_PATTERN = re.compile(r"\$?\d{1,3}(?:\.\d{2})?\b")


def menu_aware_chunk(text: str) -> list[Chunk]:
    """
    Structure-aware chunking: splits the menu into per-dish blocks by
    detecting price markers, then groups the text preceding each price
    (dish name + description) together WITH that price into one chunk.

    This avoids the core bug entirely: a dish name and its price can
    never be split across chunks, because the price is what defines
    the chunk boundary.
    """
    # Find all price occurrences and their positions
    matches = list(PRICE_PATTERN.finditer(text))
    if not matches:
        # No prices found — fall back to fixed-size chunking
        return fixed_size_chunk(text)

    chunks = []
    start = 0
    for match in matches:
        end = match.end()
        segment = text[start:end].strip()
        if segment:
            chunks.append(Chunk(text=segment, method="menu_aware"))
        start = end

    # Capture any trailing text after the last price (e.g. footnotes)
    trailing = text[start:].strip()
    if trailing:
        chunks.append(Chunk(text=trailing, method="menu_aware"))

    return chunks


def demo():
    sample_menu_text = (
        "Grilled Salmon\n"
        "Fresh Atlantic salmon fillet, grilled and served with seasonal "
        "vegetables and a lemon butter sauce, finished with fresh herbs "
        "from our garden.\n"
        "$24.99\n"
        "\n"
        "Margherita Pizza\n"
        "Classic Neapolitan-style pizza with San Marzano tomatoes, fresh "
        "mozzarella, and basil, baked in our wood-fired oven.\n"
        "$16.50\n"
        "\n"
        "Caesar Salad\n"
        "Crisp romaine lettuce tossed with our house-made Caesar dressing, "
        "shaved parmesan, and garlic croutons.\n"
        "$12.00\n"
    )

    print("=== FIXED-SIZE CHUNKING (small size, no overlap — original bug) ===")
    bad_chunks = fixed_size_chunk(sample_menu_text, chunk_size=15, overlap=0)
    for i, c in enumerate(bad_chunks):
        print(f"--- Chunk {i} ---\n{c.text}\n")

    print("=== FIXED-SIZE CHUNKING (tuned size + overlap) ===")
    tuned_chunks = fixed_size_chunk(sample_menu_text, chunk_size=60, overlap=15)
    for i, c in enumerate(tuned_chunks):
        print(f"--- Chunk {i} ---\n{c.text}\n")

    print("=== MENU-AWARE CHUNKING (structure-based, recommended) ===")
    smart_chunks = menu_aware_chunk(sample_menu_text)
    for i, c in enumerate(smart_chunks):
        print(f"--- Chunk {i} ---\n{c.text}\n")


def main():
    if len(sys.argv) < 2:
        print("No PDF path provided — running demo on sample menu text.\n")
        demo()
        return

    pdf_path = sys.argv[1]
    pages = extract_text_from_pdf(pdf_path)
    full_text = "\n".join(pages)

    print(f"Extracted {len(pages)} pages from {pdf_path}\n")

    print("=== Menu-aware chunks ===")
    chunks = menu_aware_chunk(full_text)
    for i, c in enumerate(chunks):
        print(f"--- Chunk {i} ---\n{c.text}\n")


if __name__ == "__main__":
    main()

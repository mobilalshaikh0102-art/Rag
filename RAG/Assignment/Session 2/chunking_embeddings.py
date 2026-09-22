"""
Session 2 - Chunking & Embeddings
Tasks 1-4

Install dependencies before running (see requirements at bottom / README):
    pip install sentence-transformers scikit-learn numpy
"""

import numpy as np


# ---------------------------------------------------------------------------
# TASK 1: chunk_text function
# ---------------------------------------------------------------------------
def chunk_text(text, chunk_size, overlap):
    """
    Split `text` into word-based chunks.

    Args:
        text (str): The input text to split.
        chunk_size (int): Number of words per chunk.
        overlap (int): Number of words that consecutive chunks should share.

    Returns:
        list[str]: A list of text chunks.
    """
    if chunk_size <= 0:
        raise ValueError("chunk_size must be greater than 0")
    if overlap < 0:
        raise ValueError("overlap cannot be negative")
    if overlap >= chunk_size:
        raise ValueError("overlap must be smaller than chunk_size")

    words = text.split()
    chunks = []
    start = 0
    step = chunk_size - overlap  # how far we move forward each iteration

    while start < len(words):
        end = start + chunk_size
        chunk_words = words[start:end]
        chunks.append(" ".join(chunk_words))
        if end >= len(words):
            break
        start += step

    return chunks


# ---------------------------------------------------------------------------
# Task 1 demo: test with a ~500-word sample text
# (Original sample text written for testing purposes — swap in any
#  Wikipedia paragraph of your choice; long copyrighted text is not
#  reproduced here.)
# ---------------------------------------------------------------------------
sample_500_word_text = """
The history of computing spans several centuries, beginning long before the
invention of electronic machines. Early humans used simple tools such as
tally sticks and the abacus to keep track of numbers and perform basic
arithmetic. These devices, while primitive, represented the first attempts
to externalize calculation, allowing people to solve problems that would
have been difficult to manage using memory alone. Over time, mechanical
calculating devices became more sophisticated, culminating in inventions
such as Blaise Pascal's mechanical calculator in the seventeenth century
and Charles Babbage's Analytical Engine in the nineteenth century, which is
often considered a conceptual ancestor of the modern computer.

The twentieth century brought rapid advances that transformed computing
from a mechanical curiosity into a foundational technology of modern life.
The development of the vacuum tube enabled the construction of the first
electronic computers, such as ENIAC, which could perform calculations at
speeds unimaginable to earlier mechanical devices. These early machines
were enormous, consumed vast amounts of power, and required teams of
engineers to operate and maintain. Despite their limitations, they proved
that electronic computation was not only possible but practical for solving
complex problems in science, engineering, and defense.

The invention of the transistor in the middle of the twentieth century
marked a turning point. Transistors were smaller, more reliable, and far
more energy efficient than vacuum tubes, and they paved the way for the
integrated circuit. Integrated circuits allowed engineers to place many
transistors onto a single chip, dramatically increasing computing power
while shrinking the physical size of machines. This period saw the rise of
mainframe computers used by large corporations and governments, followed
by the minicomputer, which brought computing capability to smaller
organizations and research labs.

The personal computer revolution of the late twentieth century changed
computing from a specialized tool used by institutions into something
accessible to ordinary individuals. Companies introduced affordable
machines for homes and small businesses, accompanied by user-friendly
operating systems and software applications. This shift was accompanied by
the growth of programming languages, which made it easier for developers to
write software without needing deep knowledge of hardware architecture.
Graphical user interfaces further lowered the barrier to entry, enabling
people without technical training to use computers for tasks such as word
processing, spreadsheets, and games.

The emergence of the internet in the final decades of the twentieth century
connected computers across the globe, enabling instantaneous communication
and the exchange of information on a scale never before possible. This
connectivity gave rise to the World Wide Web, search engines, and
eventually social media platforms that reshaped how people communicate,
work, and access information. Mobile computing, powered by smartphones and
tablets, extended these capabilities beyond the desktop, placing powerful
computing devices in the pockets of billions of people worldwide.

In recent years, the field has been shaped by advances in artificial
intelligence and machine learning, which allow computers to recognize
patterns, make predictions, and generate content in ways that were
previously thought to require human intelligence. Cloud computing has
allowed organizations to access vast computing resources without owning
physical hardware, while advances in specialized processors have
accelerated the training of large-scale models. As computing continues to
evolve, it remains deeply intertwined with nearly every aspect of modern
society, from communication and commerce to science and entertainment.
""".strip()

print("=" * 70)
print("TASK 1: chunk_text() demo on ~500-word sample text")
print("=" * 70)
word_count = len(sample_500_word_text.split())
print(f"Sample text word count: {word_count}\n")

chunks = chunk_text(sample_500_word_text, chunk_size=100, overlap=20)
print(f"Number of chunks produced (chunk_size=100, overlap=20): {len(chunks)}\n")
for i, c in enumerate(chunks, 1):
    print(f"--- Chunk {i} ({len(c.split())} words) ---")
    print(c)
    print()


# ---------------------------------------------------------------------------
# TASK 2: Chunk a privacy-policy-style text into 100-word chunks, 20-word overlap
# ---------------------------------------------------------------------------
# NOTE: Paste the ACTUAL privacy policy text you copied from Instagram's or
# Zomato's privacy policy page into `privacy_policy_text` below. A short
# generic placeholder is used here so the script runs end-to-end; replace it
# with the real text for your submission.
privacy_policy_text = """
We collect information you provide directly to us when you create an
account, update your profile, place an order, or otherwise communicate with
us. This may include your name, email address, phone number, delivery
address, payment details, and any other information you choose to share.
We also automatically collect certain information when you use our app,
such as your device type, operating system, IP address, location data, and
how you interact with our services. This information helps us understand
usage patterns and improve the overall experience for all users.

We use the information we collect to provide, maintain, and improve our
services, process transactions, send order updates, personalize content and
recommendations, and communicate with you about promotions, new features,
or policy changes. We may also use your data to detect and prevent fraud,
enforce our terms of service, and comply with legal obligations. In some
cases, we combine information from different sources to build a more
complete picture of how our services are used, which allows us to make
better decisions about product design and customer support.

We may share your information with delivery partners, restaurant partners,
payment processors, and other third-party service providers who help us
operate our platform. These partners are contractually obligated to protect
your data and use it only for the purposes we specify. We do not sell your
personal information to advertisers. However, we may share aggregated or
anonymized data with business partners for analytics and marketing
purposes. You have the right to access, correct, or delete your personal
information at any time by contacting our support team or using the
privacy settings available within the app.
""".strip()

print("=" * 70)
print("TASK 2: Privacy policy chunking (chunk_size=100, overlap=20)")
print("=" * 70)
policy_chunks = chunk_text(privacy_policy_text, chunk_size=100, overlap=20)
print(f"Total chunks produced: {len(policy_chunks)}\n")
for i, c in enumerate(policy_chunks[:3], 1):
    print(f"--- Chunk {i} ({len(c.split())} words) ---")
    print(c)
    print()


# ---------------------------------------------------------------------------
# TASK 3: Sentence embeddings with sentence-transformers
# ---------------------------------------------------------------------------
def get_embeddings(sentences, model_name="all-MiniLM-L6-v2"):
    """Load a SentenceTransformer model and return embeddings for a list of sentences."""
    from sentence_transformers import SentenceTransformer

    model = SentenceTransformer(model_name)
    embeddings = model.encode(sentences)
    return embeddings, model


if __name__ == "__main__":
    try:
        print("=" * 70)
        print("TASK 3: Sentence embeddings (all-MiniLM-L6-v2)")
        print("=" * 70)

        food_reviews = [
            "The pizza was amazing",
            "Service was slow",
            "Loved the ambience",
        ]

        embeddings, model = get_embeddings(food_reviews)

        for sentence, vector in zip(food_reviews, embeddings):
            print(f"Sentence: {sentence!r}")
            print(f"Embedding shape: {vector.shape}")
            print(f"Embedding (first 10 dims): {vector[:10]}")
            print()

        # -------------------------------------------------------------
        # TASK 4: Cosine similarity between two sentences
        # -------------------------------------------------------------
        print("=" * 70)
        print("TASK 4: Cosine similarity between two burger sentences")
        print("=" * 70)

        from sklearn.metrics.pairwise import cosine_similarity

        sentence_a = "The burger was delicious"
        sentence_b = "I enjoyed the burger a lot"

        vec_a = model.encode([sentence_a])
        vec_b = model.encode([sentence_b])

        similarity = cosine_similarity(vec_a, vec_b)[0][0]

        print(f"Sentence A: {sentence_a!r}")
        print(f"Sentence B: {sentence_b!r}")
        print(f"Cosine similarity: {similarity:.4f}")

        if similarity > 0.7:
            interpretation = (
                "High similarity — the two sentences are semantically close. "
                "Even though they use different words ('delicious' vs. "
                "'enjoyed ... a lot'), the model captures that both express "
                "positive sentiment about the same subject (the burger)."
            )
        elif similarity > 0.4:
            interpretation = (
                "Moderate similarity — the sentences share the same topic "
                "and a broadly positive tone, but differ enough in phrasing "
                "that the model doesn't treat them as near-duplicates."
            )
        else:
            interpretation = (
                "Low similarity — despite discussing the same topic, the "
                "model does not consider these sentences closely related."
            )

        print(f"\nInterpretation: {interpretation}")

    except ImportError as e:
        print("\n[!] Missing dependency:", e)
        print("Install with: pip install sentence-transformers scikit-learn")
    except Exception as e:
        print("\n[!] Error while running Task 3/4:", repr(e))

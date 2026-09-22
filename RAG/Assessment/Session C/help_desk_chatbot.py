"""
Section C - Mini Capstone: Food Delivery Help Desk Chatbot (RAG-Powered Console App)

Install dependencies:
    pip install faiss-cpu sentence-transformers numpy

Run:
    python help_desk_chatbot.py
"""

import os
import datetime
import numpy as np
import faiss
from sentence_transformers import SentenceTransformer

LOG_FILE = "session_log.txt"

# ===========================================================================
# 1. POLICY DOCUMENT (500+ words) -- refund, cancellation, delivery rules
# ===========================================================================
POLICY_TEXT = """
Our food delivery platform is committed to ensuring a smooth, fair, and
transparent experience for every customer. This policy explains our rules
for refunds, order cancellations, and delivery windows so you always know
what to expect if something goes wrong with your order.

Refund Policy: If you receive a missing item, a wrong item, or food that
arrives in poor condition, you may be eligible for a full or partial refund
depending on the nature of the issue. Missing item complaints must be
reported within 24 hours of delivery through the app's Help section. Once
reported, our support team reviews the order details and, if approved,
issues a refund to your original payment method within 5 to 7 business
days. Refunds for wrong items follow the same 24-hour reporting window and
require the customer to confirm the incorrect item received. Refunds for
poor food quality require a photo of the item and are reviewed on a
case-by-case basis by our quality team. Refunds are not issued for
change-of-mind cancellations placed after the restaurant has already begun
preparing the order. Repeated refund requests on the same account may
trigger a manual review before future refunds are approved.

Delivery Window Policy: Standard delivery windows range from 30 to 45
minutes from the time the restaurant confirms the order, though actual
times may vary based on distance, weather conditions, traffic, and
restaurant volume during peak hours. If your order exceeds the estimated
delivery window by more than 20 minutes, you are entitled to a delivery
credit that will be applied automatically to your next order. Customers can
track their order in real time through the "My Orders" section of the app,
which displays the current status: order confirmed, being prepared, out for
delivery, or delivered. If a delivery partner is unable to reach your
location after multiple attempts, they will try to contact you directly
before returning the order to the restaurant, in which case a refund will
be issued.

Order Cancellation Policy: Orders can be cancelled free of charge within 5
minutes of being placed, as long as the restaurant has not yet begun
preparation. After this window, cancellation may incur a partial charge to
cover ingredients and preparation costs already incurred by the restaurant.
Once an order has been picked up by a delivery partner, it can no longer be
cancelled through the app and customers should contact support directly.
If a restaurant is unable to fulfill an order due to closure, high demand,
or item unavailability, the order will be automatically cancelled and fully
refunded without any action required from the customer. For accounts with
a pattern of repeated or abusive cancellations, our platform reserves the
right to temporarily restrict cancellation privileges to protect restaurant
partners from unnecessary losses.

Contact and Escalation: Customers who are not satisfied with the outcome of
a refund or cancellation request can escalate the issue through the "Contact
Support" option in the Help section, where a live agent will review the
case in more detail and respond within 24 hours.
""".strip()


# ===========================================================================
# 2. FEW-SHOT COMPLAINT CLASSIFICATION BANK (at least 4 labelled examples)
# ===========================================================================
EXAMPLES = [
    {"input": "My food arrived almost an hour after the promised time.", "output": "Late Delivery"},
    {"input": "I ordered a chicken burger but received a veg burger instead.", "output": "Wrong Item"},
    {"input": "One of the drinks I paid for was not in the bag.", "output": "Missing Item"},
    {"input": "The pizza was cold and soggy when it arrived.", "output": "Poor Quality"},
]

CLASSIFY_INSTRUCTION = (
    "You are a classifier that categorizes food delivery complaints into "
    "exactly one of the following categories: Late Delivery, Wrong Item, "
    "Missing Item, Poor Quality.\n"
    "Read the complaint and respond with only the category name.\n"
)


# ===========================================================================
# 3. Chunking utility
# ===========================================================================
def chunk_text(text: str, chunk_size: int = 100, overlap: int = 20) -> list:
    """Split text into overlapping word-based chunks."""
    words = text.split()
    chunks = []
    step = chunk_size - overlap

    start = 0
    while start < len(words):
        end = start + chunk_size
        chunks.append(" ".join(words[start:end]))
        if end >= len(words):
            break
        start += step

    return chunks


# ===========================================================================
# 4. Load model, build FAISS indexes (policy chunks + few-shot bank)
# ===========================================================================
print("Loading embedding model and building indexes... please wait.\n")
model = SentenceTransformer("all-MiniLM-L6-v2")

# --- Policy chunk index ---
policy_chunks = chunk_text(POLICY_TEXT, chunk_size=100, overlap=20)
policy_embeddings = np.array(model.encode(policy_chunks)).astype("float32")

policy_index = faiss.IndexFlatL2(policy_embeddings.shape[1])
policy_index.add(policy_embeddings)

assert policy_index.ntotal == len(policy_chunks), "Policy index size mismatch."
print(f"Policy document loaded: {len(POLICY_TEXT.split())} words -> "
      f"{len(policy_chunks)} chunks indexed.\n")

# --- Few-shot example bank index (used to find closest matching example) ---
example_texts = [ex["input"] for ex in EXAMPLES]
example_embeddings = np.array(model.encode(example_texts)).astype("float32")

example_index = faiss.IndexFlatL2(example_embeddings.shape[1])
example_index.add(example_embeddings)


# ===========================================================================
# 5. RAG retrieval + prompt assembly
# ===========================================================================
def retrieve(query: str, k: int = 3) -> list:
    """Return the top-k most relevant policy chunks for a query."""
    query_vector = model.encode([query]).astype("float32")
    _, indices = policy_index.search(query_vector, k)
    return [policy_chunks[idx] for idx in indices[0] if idx != -1]


def build_rag_prompt(query: str, retrieved_chunks: list) -> str:
    """Assemble system instruction -> numbered context -> question -> grounding rule."""
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
    return (
        f"{system_instruction}\n\n"
        f"----- Retrieved Context -----\n{context_blocks}\n\n"
        f"----- User Question -----\n{query}\n\n"
        f"----- Instruction -----\n{grounding_instruction}"
    )


# ===========================================================================
# 6. Few-shot classification prompt + prediction
# ===========================================================================
def build_few_shot_prompt(complaint_text: str) -> str:
    """Build instruction + labelled examples + new complaint with blank Output."""
    parts = [CLASSIFY_INSTRUCTION]
    for ex in EXAMPLES:
        parts.append(f"Input: {ex['input']}")
        parts.append(f"Output: {ex['output']}")
        parts.append("")
    parts.append(f"Input: {complaint_text}")
    parts.append("Output:")
    return "\n".join(parts)


def classify_complaint(complaint_text: str):
    """
    Simulate LLM classification by finding the nearest labelled example in
    the embedding space. Returns (predicted_label, closest_example_text).
    In production, build_few_shot_prompt's output would instead be sent to
    an LLM API and its completion parsed as the predicted label.
    """
    query_vector = model.encode([complaint_text]).astype("float32")
    _, indices = example_index.search(query_vector, 1)
    closest_idx = indices[0][0]
    closest_example = EXAMPLES[closest_idx]
    return closest_example["output"], closest_example["input"]


# ===========================================================================
# 7. Input validation
# ===========================================================================
def validate_non_empty(text: str, field_name: str) -> str:
    """Raise ValueError if text is empty/blank after stripping."""
    cleaned = text.strip()
    if not cleaned:
        raise ValueError(f"{field_name} cannot be empty. Please enter some text.")
    return cleaned


# ===========================================================================
# 8. Session logging
# ===========================================================================
def log_interaction(mode: str, query_text: str, output_text: str) -> None:
    """Append one interaction to the plain-text session log file."""
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(f"[{timestamp}] MODE: {mode}\n")
        f.write(f"QUERY: {query_text}\n")
        f.write(f"OUTPUT: {output_text}\n")
        f.write("-" * 60 + "\n")


# ===========================================================================
# 9. Menu handlers
# ===========================================================================
def handle_rag_question() -> bool:
    """Returns True if a valid interaction was logged, False otherwise."""
    try:
        raw_question = input("\nEnter your policy question: ")
        question = validate_non_empty(raw_question, "Question")
    except ValueError as e:
        print(f"[Input Error] {e}")
        return False

    retrieved_chunks = retrieve(question, k=3)

    print("\n----- Retrieved Chunks -----")
    for i, chunk in enumerate(retrieved_chunks, start=1):
        print(f"[Chunk {i}]\n{chunk}\n")

    prompt = build_rag_prompt(question, retrieved_chunks)
    print("----- Assembled RAG Prompt -----")
    print(prompt)

    # Placeholder simulated answer (would be the LLM's real response)
    simulated_answer = "[Simulated Answer] (This is where the LLM's response would appear.)"
    print("\n----- Simulated Answer -----")
    print(simulated_answer)

    log_interaction("RAG", question, simulated_answer)
    return True


def handle_classification() -> bool:
    """Returns True if a valid interaction was logged, False otherwise."""
    try:
        raw_complaint = input("\nEnter the complaint text to classify: ")
        complaint = validate_non_empty(raw_complaint, "Complaint")
    except ValueError as e:
        print(f"[Input Error] {e}")
        return False

    prompt = build_few_shot_prompt(complaint)
    print("\n----- Few-Shot Classification Prompt -----")
    print(prompt)

    predicted_label, closest_example = classify_complaint(complaint)

    print("\n----- Prediction -----")
    print(f"Predicted Category : {predicted_label}")
    print(f"Closest Example    : \"{closest_example}\"")

    output_summary = f"Predicted={predicted_label}; ClosestExample={closest_example}"
    log_interaction("Classify", complaint, output_summary)
    return True


# ===========================================================================
# 10. Main menu loop
# ===========================================================================
def print_menu():
    print("\n" + "=" * 60)
    print("FOOD DELIVERY HELP DESK CHATBOT")
    print("=" * 60)
    print("1. Ask a policy question (RAG)")
    print("2. Classify a complaint (Few-Shot)")
    print("3. Exit")


def main():
    rag_count = 0
    classify_count = 0

    while True:
        print_menu()
        choice = input("Select an option (1-3): ").strip()

        if choice == "1":
            if handle_rag_question():
                rag_count += 1

        elif choice == "2":
            if handle_classification():
                classify_count += 1

        elif choice == "3":
            print("\n" + "=" * 60)
            print("SESSION SUMMARY")
            print("=" * 60)
            print(f"Policy questions asked : {rag_count}")
            print(f"Complaints classified   : {classify_count}")
            print(f"Session log saved to    : {os.path.abspath(LOG_FILE)}")
            print("Goodbye!")
            break

        else:
            print("[Input Error] Please enter 1, 2, or 3.")


if __name__ == "__main__":
    main()

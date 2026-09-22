"""
Task 2: Few-Shot Complaint Classifier Prompt Builder

No external dependencies required -- pure Python standard library.

Run:
    python few_shot_classifier.py
"""

# ---------------------------------------------------------------------------
# Labelled few-shot examples covering all four complaint categories
# ---------------------------------------------------------------------------
EXAMPLES = [
    {
        "input": "My food arrived almost an hour after the promised time.",
        "output": "Late Delivery",
    },
    {
        "input": "I ordered a chicken burger but received a veg burger instead.",
        "output": "Wrong Item",
    },
    {
        "input": "One of the drinks I paid for was not in the bag.",
        "output": "Missing Item",
    },
    {
        "input": "The pizza was cold and soggy when it arrived.",
        "output": "Poor Quality",
    },
]

INSTRUCTION = (
    "You are a classifier that categorizes food delivery complaints into "
    "exactly one of the following categories: Late Delivery, Wrong Item, "
    "Missing Item, Poor Quality.\n"
    "Read the complaint and respond with only the category name.\n"
)


def add_example(text: str, label: str) -> None:
    """Append a new labelled example to the EXAMPLES list."""
    EXAMPLES.append({"input": text, "output": label})


def build_few_shot_prompt(complaint_text: str) -> str:
    """
    Build a few-shot prompt: instruction + labelled examples +
    the new complaint with a blank Output line for the LLM to complete.
    """
    prompt_parts = [INSTRUCTION]

    for example in EXAMPLES:
        prompt_parts.append(f"Input: {example['input']}")
        prompt_parts.append(f"Output: {example['output']}")
        prompt_parts.append("")  # blank line between examples

    # New complaint to classify -- blank Output line for the LLM
    prompt_parts.append(f"Input: {complaint_text}")
    prompt_parts.append("Output:")

    return "\n".join(prompt_parts)


def main():
    # --- Test case 1 ---
    complaint_1 = "The delivery guy handed me someone else's order entirely."
    print("=" * 60)
    print("TEST CASE 1")
    print("=" * 60)
    print(build_few_shot_prompt(complaint_1))
    print()

    # --- Test case 2 ---
    complaint_2 = "My order took over 90 minutes and the driver never called."
    print("=" * 60)
    print("TEST CASE 2")
    print("=" * 60)
    print(build_few_shot_prompt(complaint_2))
    print()

    # --- Add a new example dynamically ---
    add_example(
        "The fries were stale and clearly not freshly made.",
        "Poor Quality",
    )

    # --- Test case 3: confirm the new example now appears in the prompt ---
    complaint_3 = "I received someone else's bag with a different restaurant's food."
    print("=" * 60)
    print("TEST CASE 3 (after add_example call)")
    print("=" * 60)
    print(build_few_shot_prompt(complaint_3))


if __name__ == "__main__":
    main()

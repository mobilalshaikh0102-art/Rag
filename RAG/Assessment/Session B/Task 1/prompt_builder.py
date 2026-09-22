"""
Task 1: Structured Prompt Builder for Food Delivery Chatbot

No external dependencies required -- pure Python standard library.

Run:
    python prompt_builder.py
"""

# ---------------------------------------------------------------------------
# System prompt: defines the LLM's role, tone, and response constraints
# ---------------------------------------------------------------------------
SYSTEM_PROMPT = """You are a professional and helpful customer support agent \
for a food delivery platform. You assist customers with order-related \
issues such as late deliveries, missing items, wrong items, and damaged items. \
Always respond in a polite, empathetic, and solution-oriented tone. \
Keep every response concise and under 80 words."""

# ---------------------------------------------------------------------------
# User message template: accepts customer_name, order_id, and issue_type
# ---------------------------------------------------------------------------
USER_MESSAGE_TEMPLATE = """Customer Name: {customer_name}
Order ID: {order_id}
Issue Type: {issue_type}

Please generate a support response addressing this customer's issue."""

# Allowed values for issue_type
ALLOWED_ISSUE_TYPES = {"late delivery", "missing item", "wrong item", "damaged item"}


def validate_issue_type(issue_type: str) -> None:
    """Raise ValueError if issue_type is not one of the allowed values."""
    if issue_type not in ALLOWED_ISSUE_TYPES:
        allowed = ", ".join(sorted(ALLOWED_ISSUE_TYPES))
        raise ValueError(
            f"Invalid issue_type: '{issue_type}'. "
            f"Allowed values are: {allowed}."
        )


def build_prompt(customer_name: str, order_id: str, issue_type: str) -> str:
    """Validate inputs and build the full system + user prompt pair."""
    validate_issue_type(issue_type)

    user_message = USER_MESSAGE_TEMPLATE.format(
        customer_name=customer_name,
        order_id=order_id,
        issue_type=issue_type,
    )

    full_prompt = (
        "----- SYSTEM PROMPT -----\n"
        f"{SYSTEM_PROMPT}\n\n"
        "----- USER MESSAGE -----\n"
        f"{user_message}"
    )
    return full_prompt


def run_test_case(customer_name: str, order_id: str, issue_type: str) -> None:
    """Wrap prompt construction in try-except so invalid input never crashes."""
    print("=" * 60)
    try:
        prompt = build_prompt(customer_name, order_id, issue_type)
        print(prompt)
    except ValueError as e:
        print(f"[Error] Could not build prompt: {e}")
    print("=" * 60)
    print()


def main():
    # Test case 1: valid issue_type
    run_test_case(
        customer_name="Aarav Mehta",
        order_id="FD10293",
        issue_type="late delivery",
    )

    # Test case 2: valid issue_type
    run_test_case(
        customer_name="Priya Sharma",
        order_id="FD10499",
        issue_type="missing item",
    )

    # Test case 3: valid issue_type
    run_test_case(
        customer_name="Rohan Kapoor",
        order_id="FD10711",
        issue_type="damaged item",
    )

    # Test case 4: invalid issue_type -- triggers ValueError, handled gracefully
    run_test_case(
        customer_name="Neha Gupta",
        order_id="FD10850",
        issue_type="payment issue",
    )


if __name__ == "__main__":
    main()






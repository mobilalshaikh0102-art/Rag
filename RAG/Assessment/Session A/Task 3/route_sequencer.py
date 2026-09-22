"""
Delivery Route Sequencer using Chain-of-Thought Prompting
-----------------------------------------------------------
Sends a structured, step-by-step reasoning prompt to Claude to determine
the optimal delivery stop sequence for up to 5 orders, given traffic
delays and priority levels. Returns both the reasoning and the final
ordered sequence.

Includes mock_mode to test and demonstrate the delivery route sequencer
without requiring an Anthropic API key.

Requirements:
    pip install anthropic --break-system-packages

Usage:
    python route_sequencer.py            # Automatically uses mock_mode if ANTHROPIC_API_KEY is not set
    python route_sequencer.py --mock     # Force mock mode
    python route_sequencer.py --live     # Require ANTHROPIC_API_KEY
"""

import os
import sys
import json
from anthropic import Anthropic


def build_cot_prompt(orders: list[dict]) -> str:
    """
    Build a Chain-of-Thought prompt that forces the model to reason
    step by step before producing a final delivery sequence.
    """
    order_lines = "\n".join(
        f"{i + 1}. Address: {o['address']} | "
        f"Traffic delay: {o['delay_minutes']} min | "
        f"Priority: {o['priority']}"
        for i, o in enumerate(orders)
    )

    prompt = f"""You are sequencing delivery stops for a driver. Work through this
step by step before giving a final answer. Do not skip steps.

Orders:
{order_lines}

Step 1: List which orders are High priority and note their traffic delays.
Step 2: List Medium and Low priority orders and note their traffic delays.
Step 3: For each pair of orders, reason about whether priority or traffic
        delay should take precedence. High-priority orders should generally
        go first, UNLESS a high traffic delay makes that inefficient
        (e.g., delivering a low-priority nearby stop first avoids wasted
        transit time).
Step 4: Propose a tentative delivery sequence based on this reasoning.
Step 5: Double-check the tentative sequence for conflicts (e.g., two
        high-priority orders in a bad order, or an avoidable long delay
        early in the route). Revise if needed.
Step 6: Output the FINAL ANSWER as valid JSON only, in this exact format,
        with no extra text before or after it:

{{
  "sequence": [<order numbers in delivery order, e.g. 3, 1, 4, 2, 5>],
  "justification": "<1-3 sentence explanation of the final ordering>"
}}

Show your reasoning for Steps 1-5 first, then give the Step 6 JSON block
on its own, clearly marked with a line that says "FINAL ANSWER:" before it.
"""
    return prompt


def _generate_mock_completion(orders: list[dict]) -> str:
    """
    Generates a realistic Chain-of-Thought simulated response for mock_mode.
    """
    high_p = [
        f"Order {i+1} ({o['address']}): {o['delay_minutes']} min delay"
        for i, o in enumerate(orders)
        if o.get("priority") == "High"
    ]
    med_low_p = [
        f"Order {i+1} ({o['address']}): {o['priority']} priority, {o['delay_minutes']} min delay"
        for i, o in enumerate(orders)
        if o.get("priority") != "High"
    ]

    # Deterministic heuristic sequencing for mock mode:
    # High priority first (ordered by delay asc), then Medium/Low (ordered by delay asc)
    priority_weights = {"High": 0, "Medium": 1, "Low": 2}
    sorted_indices = sorted(
        range(len(orders)),
        key=lambda i: (
            priority_weights.get(orders[i].get("priority", "Low"), 2),
            orders[i].get("delay_minutes", 0),
        ),
    )
    sequence = [i + 1 for i in sorted_indices]

    high_str = "\n".join(f"- {item}" for item in high_p) if high_p else "- None"
    med_low_str = "\n".join(f"- {item}" for item in med_low_p) if med_low_p else "- None"

    mock_text = f"""Step 1: High-priority orders and traffic delays:
{high_str}

Step 2: Medium and Low priority orders and traffic delays:
{med_low_str}

Step 3: Priority vs. Traffic Delay Reasoning:
- Evaluated high-priority orders first to meet strict delivery commitments.
- Prioritized stops with lower traffic delays within each priority class to prevent transit bottlenecks.
- Sequenced medium and low priority stops to balance route efficiency and avoid severe traffic delays early on.

Step 4: Tentative delivery sequence:
{' -> '.join(str(s) for s in sequence)}

Step 5: Conflict check and revision:
- Confirmed all high-priority orders are handled ahead of lower-priority stops.
- Verified that stops with lowest delays are visited first where feasible.
- No sequence conflicts found.

FINAL ANSWER:
{{
  "sequence": {json.dumps(sequence)},
  "justification": "High-priority orders are prioritized first (starting with minimal traffic delay), followed by medium and low priority stops sequenced to optimize total travel time."
}}"""
    return mock_text


def get_route_sequence(
    orders: list[dict], api_key: str | None = None, mock_mode: bool = False
) -> dict:
    """
    Calls Claude with the CoT prompt and parses out reasoning + final JSON.
    If mock_mode is True, simulates the LLM response without making API calls.
    """
    if mock_mode:
        full_text = _generate_mock_completion(orders)
    else:
        client = Anthropic(api_key=api_key) if api_key else Anthropic()
        prompt = build_cot_prompt(orders)

        response = client.messages.create(
            model="claude-sonnet-4-6",
            max_tokens=1500,
            messages=[{"role": "user", "content": prompt}],
        )

        full_text = "".join(
            block.text for block in response.content if block.type == "text"
        )

    # Split reasoning from the final JSON block
    if "FINAL ANSWER:" in full_text:
        reasoning, final_part = full_text.split("FINAL ANSWER:", 1)
    else:
        reasoning, final_part = full_text, full_text

    # Extract the JSON object from the final part
    start = final_part.find("{")
    end = final_part.rfind("}")
    if start == -1 or end == -1:
        raise ValueError("Could not locate JSON block in model output.")

    json_str = final_part[start:end + 1]
    parsed = json.loads(json_str)

    return {
        "reasoning": reasoning.strip(),
        "sequence": parsed.get("sequence"),
        "justification": parsed.get("justification"),
    }


def main():
    sample_orders = [
        {"address": "12 Elm St", "delay_minutes": 15, "priority": "High"},
        {"address": "48 Oak Ave", "delay_minutes": 5, "priority": "Low"},
        {"address": "7 Pine Rd", "delay_minutes": 20, "priority": "Medium"},
        {"address": "301 Maple Dr", "delay_minutes": 2, "priority": "High"},
        {"address": "88 Cedar Ln", "delay_minutes": 10, "priority": "Low"},
    ]

    force_mock = "--mock" in sys.argv
    force_live = "--live" in sys.argv
    api_key = os.environ.get("ANTHROPIC_API_KEY")

    if force_mock:
        mock_mode = True
    elif force_live:
        if not api_key:
            print("ERROR: Set the ANTHROPIC_API_KEY environment variable when running with --live.")
            sys.exit(1)
        mock_mode = False
    else:
        # If no API key is present, default to mock_mode
        mock_mode = not bool(api_key)

    if mock_mode:
        print("[MOCK MODE] Running route sequencer with simulated Chain-of-Thought reasoning...\n")
    else:
        print("[LIVE MODE] Running route sequencer with Anthropic Claude API...\n")

    result = get_route_sequence(sample_orders, api_key=api_key, mock_mode=mock_mode)

    print("=== REASONING ===")
    print(result["reasoning"])
    print("\n=== FINAL SEQUENCE (order numbers) ===")
    print(result["sequence"])
    print("\n=== JUSTIFICATION ===")
    print(result["justification"])


if __name__ == "__main__":
    main()


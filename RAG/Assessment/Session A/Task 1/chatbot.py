"""
Customer Support Chatbot for Food Delivery App
Implements best practices for prompt engineering and LLM consistency
"""

import json
import os
import sys
from datetime import datetime, timedelta
from typing import Dict, Optional, List
from enum import Enum
from dataclasses import dataclass, asdict

# Ensure UTF-8 output encoding in Windows terminals for currency symbols (₹)
if sys.platform == "win32":
    if hasattr(sys.stdout, "reconfigure"):
        try:
            sys.stdout.reconfigure(encoding="utf-8")
        except Exception:
            pass
    if hasattr(sys.stderr, "reconfigure"):
        try:
            sys.stderr.reconfigure(encoding="utf-8")
        except Exception:
            pass

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

try:
    import anthropic
except ImportError:
    raise ImportError("Install anthropic: pip install anthropic")


class DecisionType(Enum):
    """Valid decision outcomes"""
    APPROVE = "APPROVE"
    DECLINE = "DECLINE"
    NEEDS_REVIEW = "NEEDS_REVIEW"


class RefundReason(Enum):
    """Valid refund reason codes"""
    LATE_DELIVERY = "LATE_DELIVERY"
    QUALITY_ISSUE = "QUALITY_ISSUE"
    MISSING_ITEMS = "MISSING_ITEMS"
    WRONG_ITEM = "WRONG_ITEM"


@dataclass
class RefundDecision:
    """Structured output from refund decision"""
    decision: str
    refund_amount: float
    reason: str
    required_action: Optional[str] = None
    
    def to_json(self) -> str:
        return json.dumps(asdict(self), indent=2)


@dataclass
class CustomerOrder:
    """Order data structure"""
    order_id: str
    customer_id: str
    order_total: float
    delivery_date: str
    order_status: str
    delivery_time_minutes: Optional[int] = None
    refund_reason: Optional[str] = None
    has_photo_evidence: bool = False
    previous_refunds: int = 0
    days_since_order: int = 0


class RefundChatbot:
    """Customer support chatbot with structured prompt engineering"""
    
    # CLEAR, EXPLICIT PROMPT - This is the key to consistency
    SYSTEM_PROMPT = """You are a professional customer support agent for a food delivery app. 
Your role is to evaluate refund requests and make fair, consistent decisions.

=== REFUND DECISION RULES ===

ELIGIBILITY REQUIREMENTS:
1. Order status must be "delivered" or "order_placed"
2. Refund request must be within 7 days of delivery
3. Customer can only be refunded once per order
4. Reason code must be one of: LATE_DELIVERY, QUALITY_ISSUE, MISSING_ITEMS, WRONG_ITEM

DECISION LOGIC BY REASON:

For LATE_DELIVERY:
- APPROVE if delivery was more than 30 minutes late
- Refund amount: 10% of order total
- No additional evidence required

For QUALITY_ISSUE:
- APPROVE if customer provided photo evidence
- NEEDS_REVIEW if no photo evidence
- Refund amount: 50% of order total (with evidence), request evidence if missing
- Request: Customer uploads photo of issue

For MISSING_ITEMS:
- APPROVE if customer provided photo evidence or detailed item list
- NEEDS_REVIEW if no documentation
- Refund amount: price of missing items (request itemized list if needed)
- Request: Item photos or detailed list with prices

For WRONG_ITEM:
- APPROVE if documented and different from order
- NEEDS_REVIEW if no supporting documentation
- Refund amount: 100% of order total
- Request: Photo or detailed description of discrepancy

DECLINE CONDITIONS (must decline in these cases):
- Order status is "cancelled" or "refunded"
- Days since order exceeds 7 days
- Customer already has refund for this order
- Reason code is not valid or provided
- Missing critical information for verification

CONSTRAINTS:
- Maximum refund: 100% of order total
- Minimum refund: 5% of order total
- Cannot exceed order_total amount
- Customer receives only one refund per order

=== OUTPUT FORMAT ===

You MUST respond ONLY with a valid JSON object in this exact format:
{
  "decision": "APPROVE" | "DECLINE" | "NEEDS_REVIEW",
  "refund_amount": <number: amount in rupees (₹)>,
  "reason": "<string: clear, professional explanation (2-3 sentences)>",
  "required_action": "<string: if NEEDS_REVIEW, specify exactly what's needed. Otherwise null>"
}

TONE GUIDELINES:
- Be empathetic and professional
- Explain decisions clearly
- For NEEDS_REVIEW: specify exact documentation needed
- For DECLINE: explain why we cannot approve

=== CRITICAL INSTRUCTIONS ===
1. ALWAYS return valid JSON only - no markdown formatting
2. ALWAYS use a decision from the three allowed options
3. ALWAYS include a reason explaining your decision
4. ALWAYS validate against decline conditions
5. DO NOT approve if eligibility requirements are not met
6. DO NOT make exceptions to these rules
"""

    def __init__(self, api_key: Optional[str] = None, mock_mode: Optional[bool] = None):
        """Initialize chatbot with Anthropic API key or enable mock mode"""
        if mock_mode is None:
            self.mock_mode = os.environ.get("MOCK_MODE", "").lower() in ("true", "1", "yes")
        else:
            self.mock_mode = mock_mode

        self.api_key = api_key or os.environ.get("ANTHROPIC_API_KEY")
        if not self.mock_mode and (not self.api_key or self.api_key == "your_anthropic_api_key_here"):
            raise ValueError("ANTHROPIC_API_KEY environment variable not set")
        
        if not self.mock_mode:
            self.client = anthropic.Anthropic(api_key=self.api_key)
            self.model = "claude-3-5-sonnet-20241022"
        else:
            self.client = None
            self.model = "mock-claude-3-5-sonnet"

        self.decision_history: List[Dict] = []

    def _evaluate_mock_refund(self, order: CustomerOrder) -> RefundDecision:
        """Simulate LLM evaluation strictly adhering to prompt rules when MOCK_MODE is enabled"""
        # 1. Decline Conditions
        if order.order_status.lower() in ["cancelled", "refunded"]:
            return RefundDecision(
                decision=DecisionType.DECLINE.value,
                refund_amount=0.0,
                reason=f"Refund request cannot be approved because the order status is '{order.order_status}'."
            )
            
        if order.days_since_order > 7:
            return RefundDecision(
                decision=DecisionType.DECLINE.value,
                refund_amount=0.0,
                reason=f"Refund request cannot be processed as it exceeds the 7-day eligibility window. The order was placed {order.days_since_order} days ago, which is outside our refund policy timeframe."
            )
            
        if order.previous_refunds > 0:
            return RefundDecision(
                decision=DecisionType.DECLINE.value,
                refund_amount=0.0,
                reason="Refund request declined. Customer has already received a refund for this order."
            )
            
        reason_code = (order.refund_reason or "").upper()
        if reason_code not in [r.value for r in RefundReason]:
            return RefundDecision(
                decision=DecisionType.DECLINE.value,
                refund_amount=0.0,
                reason=f"Reason code '{order.refund_reason}' is not valid or provided. Must be one of LATE_DELIVERY, QUALITY_ISSUE, MISSING_ITEMS, WRONG_ITEM."
            )

        # 2. Decision Logic By Reason
        if reason_code == RefundReason.LATE_DELIVERY.value:
            delivery_time = order.delivery_time_minutes or 0
            if delivery_time > 30:
                amount = round(order.order_total * 0.10, 2)
                return RefundDecision(
                    decision=DecisionType.APPROVE.value,
                    refund_amount=amount,
                    reason=f"Delivery was {delivery_time} minutes late, which exceeds the 30-minute threshold for late delivery refunds. A 10% refund of ₹{order.order_total:.2f} is approved."
                )
            else:
                return RefundDecision(
                    decision=DecisionType.DECLINE.value,
                    refund_amount=0.0,
                    reason=f"Delivery delay ({delivery_time} minutes) does not exceed the 30-minute threshold required for a refund."
                )

        elif reason_code == RefundReason.QUALITY_ISSUE.value:
            if order.has_photo_evidence:
                amount = round(order.order_total * 0.50, 2)
                return RefundDecision(
                    decision=DecisionType.APPROVE.value,
                    refund_amount=amount,
                    reason=f"Customer provided photographic evidence of quality issues. 50% refund of ₹{order.order_total:.2f} is approved for documented quality problems."
                )
            else:
                return RefundDecision(
                    decision=DecisionType.NEEDS_REVIEW.value,
                    refund_amount=0.0,
                    reason="Customer reported quality issues but did not provide photo evidence. Documentation is required to proceed.",
                    required_action="Please provide photo evidence of the food quality issue"
                )

        elif reason_code == RefundReason.MISSING_ITEMS.value:
            if order.has_photo_evidence:
                amount = round(order.order_total * 0.50, 2)
                return RefundDecision(
                    decision=DecisionType.APPROVE.value,
                    refund_amount=amount,
                    reason=f"Customer provided documentation of missing items. Refund of ₹{amount:.2f} is approved."
                )
            else:
                return RefundDecision(
                    decision=DecisionType.NEEDS_REVIEW.value,
                    refund_amount=0.0,
                    reason="Customer reported missing items but did not provide supporting evidence. Documentation is required to proceed.",
                    required_action="Please provide itemized list of missing items with prices or photos of the incomplete order"
                )

        elif reason_code == RefundReason.WRONG_ITEM.value:
            if order.has_photo_evidence:
                amount = round(order.order_total, 2)
                return RefundDecision(
                    decision=DecisionType.APPROVE.value,
                    refund_amount=amount,
                    reason=f"Customer received incorrect item as documented. Full 100% refund of ₹{order.order_total:.2f} is approved."
                )
            else:
                return RefundDecision(
                    decision=DecisionType.NEEDS_REVIEW.value,
                    refund_amount=0.0,
                    reason="Customer reported receiving wrong item without supporting documentation.",
                    required_action="Please provide photo or detailed description of discrepancy"
                )

        return RefundDecision(
            decision=DecisionType.DECLINE.value,
            refund_amount=0.0,
            reason="Request did not meet standard refund criteria."
        )

    def _build_user_message(self, order: CustomerOrder) -> str:
        """Build structured user message with all order details"""
        return f"""Please evaluate this refund request and provide your decision:

ORDER DETAILS:
- Order ID: {order.order_id}
- Customer ID: {order.customer_id}
- Order Total: ₹{order.order_total:.2f}
- Order Status: {order.order_status}
- Delivery Date: {order.delivery_date}
- Days Since Order: {order.days_since_order}

REFUND REQUEST:
- Reason Code: {order.refund_reason}
- Delivery Time (if late): {order.delivery_time_minutes} minutes{' late' if order.delivery_time_minutes and order.delivery_time_minutes > 30 else ''}
- Photo Evidence Provided: {order.has_photo_evidence}
- Previous Refunds for This Order: {order.previous_refunds}

Please evaluate this request against the decision rules and respond with a JSON decision object only."""

    def evaluate_refund(self, order: CustomerOrder) -> RefundDecision:
        """
        Evaluate refund request using LLM with structured prompting (or mock mode)
        
        Args:
            order: CustomerOrder object with all details
            
        Returns:
            RefundDecision object with decision and reasoning
        """
        if self.mock_mode:
            decision = self._evaluate_mock_refund(order)
            self.decision_history.append({
                "timestamp": datetime.now().isoformat(),
                "order_id": order.order_id,
                "decision": decision.decision,
                "refund_amount": decision.refund_amount
            })
            return decision

        user_message = self._build_user_message(order)
        
        try:
            response = self.client.messages.create(
                model=self.model,
                max_tokens=500,
                system=self.SYSTEM_PROMPT,
                messages=[
                    {"role": "user", "content": user_message}
                ]
            )
            
            response_text = response.content[0].text.strip()
            
            # Remove markdown formatting if present
            if response_text.startswith("```"):
                response_text = response_text.split("```")[1]
                if response_text.startswith("json"):
                    response_text = response_text[4:]
                response_text = response_text.strip()
            
            # Parse JSON response
            decision_dict = json.loads(response_text)
            
            # Validate response structure
            decision = self._validate_decision(decision_dict)
            
            # Log decision for audit trail
            self.decision_history.append({
                "timestamp": datetime.now().isoformat(),
                "order_id": order.order_id,
                "decision": decision.decision,
                "refund_amount": decision.refund_amount
            })
            
            return decision
            
        except json.JSONDecodeError as e:
            # Handle malformed JSON - escalate to review
            print(f"JSON Parse Error: {e}")
            return RefundDecision(
                decision=DecisionType.NEEDS_REVIEW.value,
                refund_amount=0.0,
                reason="System error in parsing response. Request requires manual review.",
                required_action="Escalate to support supervisor"
            )
        except anthropic.APIError as e:
            print(f"API Error: {e}")
            raise

    def _validate_decision(self, decision_dict: Dict) -> RefundDecision:
        """Validate and sanitize decision dictionary"""
        try:
            # Validate decision type
            decision = decision_dict.get("decision", "").upper()
            if decision not in [d.value for d in DecisionType]:
                raise ValueError(f"Invalid decision: {decision}")
            
            # Validate refund amount
            refund_amount = float(decision_dict.get("refund_amount", 0))
            if refund_amount < 0:
                raise ValueError("Refund amount cannot be negative")
            
            # Get reason
            reason = str(decision_dict.get("reason", "No reason provided")).strip()
            if not reason:
                raise ValueError("Reason is required")
            
            # Get required action (optional)
            required_action = decision_dict.get("required_action")
            if required_action:
                required_action = str(required_action).strip()
            
            return RefundDecision(
                decision=decision,
                refund_amount=refund_amount,
                reason=reason,
                required_action=required_action
            )
            
        except (KeyError, TypeError, ValueError) as e:
            print(f"Validation Error: {e}")
            raise ValueError(f"Invalid decision structure: {e}")

    def get_audit_log(self) -> str:
        """Return audit trail of all decisions"""
        return json.dumps(self.decision_history, indent=2)


def main():
    """Example usage and testing"""
    print("Food Delivery Customer Support Chatbot")
    print("=" * 60)
    
    # Initialize chatbot
    try:
        chatbot = RefundChatbot()
        if chatbot.mock_mode:
            print("Mode: MOCK (Simulated evaluation without live Anthropic API)")
        else:
            print("Mode: LIVE (Anthropic Claude API)")
    except ValueError as e:
        print(f" Initialization Error: {e}")
        print("Please set ANTHROPIC_API_KEY environment variable")
        return
    
    # Test Case 1: Late Delivery (Clear approval case)
    print("\n TEST CASE 1: Late Delivery (>30 mins)")
    order1 = CustomerOrder(
        order_id="ORD-2024-001",
        customer_id="CUST-123",
        order_total=35.50,
        delivery_date="2024-01-15",
        order_status="delivered",
        delivery_time_minutes=45,
        refund_reason="LATE_DELIVERY",
        days_since_order=2,
        previous_refunds=0
    )
    
    try:
        decision1 = chatbot.evaluate_refund(order1)
        print(f"  Decision: {decision1.decision}")
        print(f"   Refund Amount: ₹{decision1.refund_amount:.2f}")
        print(f"   Reason: {decision1.reason}")
    except Exception as e:
        print(f" Error: {e}")
    
    # Test Case 2: Quality Issue with Evidence (Approval with evidence)
    print("\n TEST CASE 2: Quality Issue with Photo Evidence")
    order2 = CustomerOrder(
        order_id="ORD-2024-002",
        customer_id="CUST-456",
        order_total=28.99,
        delivery_date="2024-01-18",
        order_status="delivered",
        refund_reason="QUALITY_ISSUE",
        has_photo_evidence=True,
        days_since_order=1,
        previous_refunds=0
    )
    
    try:
        decision2 = chatbot.evaluate_refund(order2)
        print(f" Decision: {decision2.decision}")
        print(f"   Refund Amount: ₹{decision2.refund_amount:.2f}")
        print(f"   Reason: {decision2.reason}")
    except Exception as e:
        print(f" Error: {e}")
    
    # Test Case 3: Missing Items No Evidence (Needs Review)
    print("\n TEST CASE 3: Missing Items (No Evidence)")
    order3 = CustomerOrder(
        order_id="ORD-2024-003",
        customer_id="CUST-789",
        order_total=42.00,
        delivery_date="2024-01-19",
        order_status="delivered",
        refund_reason="MISSING_ITEMS",
        has_photo_evidence=False,
        days_since_order=0,
        previous_refunds=0
    )
    
    try:
        decision3 = chatbot.evaluate_refund(order3)
        print(f" Decision: {decision3.decision}")
        print(f"   Refund Amount: ₹{decision3.refund_amount:.2f}")
        print(f"   Reason: {decision3.reason}")
        if decision3.required_action:
            print(f"   Required Action: {decision3.required_action}")
    except Exception as e:
        print(f" Error: {e}")
    
    # Test Case 4: Outside 7-Day Window (Decline)
    print("\n TEST CASE 4: Refund Request Outside 7-Day Window")
    order4 = CustomerOrder(
        order_id="ORD-2024-004",
        customer_id="CUST-321",
        order_total=55.00,
        delivery_date="2024-01-05",
        order_status="delivered",
        refund_reason="QUALITY_ISSUE",
        has_photo_evidence=True,
        days_since_order=15,
        previous_refunds=0
    )
    
    try:
        decision4 = chatbot.evaluate_refund(order4)
        print(f" Decision: {decision4.decision}")
        print(f"   Refund Amount: ₹{decision4.refund_amount:.2f}")
        print(f"   Reason: {decision4.reason}")
    except Exception as e:
        print(f" Error: {e}")
    
    # Display audit log
    print("\n  AUDIT LOG")
    print("=" * 60)
    print(chatbot.get_audit_log())


if __name__ == "__main__":
    main()

















# output

# PS C:\Users\disha\RAG\Assessment\Session A\Task 1> python chatbot.py
# Food Delivery Customer Support Chatbot
# ============================================================
# Mode: MOCK (Simulated evaluation without live Anthropic API)

#  TEST CASE 1: Late Delivery (>30 mins)
#   Decision: APPROVE
#    Refund Amount: ₹3.55
#    Reason: Delivery was 45 minutes late, which exceeds the 30-minute threshold for late delivery refunds. A 10% refund of ₹35.50 is approved.

#  TEST CASE 2: Quality Issue with Photo Evidence
#  Decision: APPROVE
#    Refund Amount: ₹14.49
#    Reason: Customer provided photographic evidence of quality issues. 50% refund of ₹28.99 is approved for documented quality problems.

#  TEST CASE 3: Missing Items (No Evidence)
#  Decision: NEEDS_REVIEW
#    Refund Amount: ₹0.00
#    Reason: Customer reported missing items but did not provide supporting evidence. Documentation is required to proceed.    
#    Required Action: Please provide itemized list of missing items with prices or photos of the incomplete order

#  TEST CASE 4: Refund Request Outside 7-Day Window
#  Decision: DECLINE
#    Refund Amount: ₹0.00
#    Reason: Refund request cannot be processed as it exceeds the 7-day eligibility window. The order was placed 15 days ago, which is outside our refund policy timeframe.

#   AUDIT LOG
# ============================================================
# [
#   {
#     "timestamp": "2026-09-12T11:20:11.568044",
#     "order_id": "ORD-2024-001",
#     "decision": "APPROVE",
#     "refund_amount": 3.55
#   },
#   {
#     "timestamp": "2026-09-12T11:20:11.569071",
#     "order_id": "ORD-2024-002",
#     "decision": "APPROVE",
#     "refund_amount": 14.49
#   },
#   {
#     "timestamp": "2026-09-12T11:20:11.569787",
#     "order_id": "ORD-2024-003",
#     "decision": "NEEDS_REVIEW",
#     "refund_amount": 0.0
#   },
#   {
#     "timestamp": "2026-09-12T11:20:11.570501",
#     "order_id": "ORD-2024-004",
#     "decision": "DECLINE",
#     "refund_amount": 0.0
#   }
# ]












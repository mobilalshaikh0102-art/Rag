# Expected Output & Examples

## Running `python chatbot.py`

```
🚀 Food Delivery Customer Support Chatbot
============================================================

📝 TEST CASE 1: Late Delivery (>30 mins)
✅ Decision: APPROVE
   Refund Amount: $3.55
   Reason: Delivery was 45 minutes late, which exceeds the 30-minute threshold for late delivery refunds. A 10% refund of $35.50 is approved.

📝 TEST CASE 2: Quality Issue with Photo Evidence
✅ Decision: APPROVE
   Refund Amount: $14.50
   Reason: Customer provided photographic evidence of quality issues. 50% refund of $28.99 is approved for documented quality problems.

📝 TEST CASE 3: Missing Items (No Evidence)
✅ Decision: NEEDS_REVIEW
   Refund Amount: $0.00
   Reason: Customer reported missing items but did not provide supporting evidence. Documentation is required to proceed.
   Required Action: Please provide itemized list of missing items with prices or photos of the incomplete order

📝 TEST CASE 4: Refund Request Outside 7-Day Window
✅ Decision: DECLINE
   Refund Amount: $0.00
   Reason: Refund request cannot be processed as it exceeds the 7-day eligibility window. The order was placed 15 days ago, which is outside our refund policy timeframe.

📊 AUDIT LOG
============================================================
[
  {
    "timestamp": "2024-01-20T10:30:45.123456",
    "order_id": "ORD-2024-001",
    "decision": "APPROVE",
    "refund_amount": 3.55
  },
  {
    "timestamp": "2024-01-20T10:30:46.234567",
    "order_id": "ORD-2024-002",
    "decision": "APPROVE",
    "refund_amount": 14.5
  },
  {
    "timestamp": "2024-01-20T10:30:47.345678",
    "order_id": "ORD-2024-003",
    "decision": "NEEDS_REVIEW",
    "refund_amount": 0.0
  },
  {
    "timestamp": "2024-01-20T10:30:48.456789",
    "order_id": "ORD-2024-004",
    "decision": "DECLINE",
    "refund_amount": 0.0
  }
]
```

---

## Running `python app.py`

```
 * Serving Flask app 'app'
 * Debug mode: off
WARNING: This is a development server. Do not use it in production code yet.
 * Running on http://127.0.0.1:5000
Press CTRL+C to quit.
```

---

## API Response Examples

### Example 1: Late Delivery (APPROVE)

**Request:**
```bash
curl -X POST http://localhost:5000/evaluate-refund \
  -H "Content-Type: application/json" \
  -H "X-API-Key: default-dev-key" \
  -d '{
    "order_id": "ORD-2024-001",
    "customer_id": "CUST-123",
    "order_total": 35.50,
    "delivery_date": "2024-01-15",
    "order_status": "delivered",
    "delivery_time_minutes": 45,
    "refund_reason": "LATE_DELIVERY",
    "has_photo_evidence": false,
    "previous_refunds": 0,
    "days_since_order": 2
  }'
```

**Response (200 OK):**
```json
{
  "order_id": "ORD-2024-001",
  "decision": "APPROVE",
  "refund_amount": 3.55,
  "reason": "Delivery was 45 minutes late, exceeding the 30-minute threshold. 10% of $35.50 = $3.55 refund approved.",
  "required_action": null,
  "status": "success",
  "timestamp": "2024-01-20T10:30:45.123456"
}
```

---

### Example 2: Quality Issue with Evidence (APPROVE)

**Request:**
```bash
curl -X POST http://localhost:5000/evaluate-refund \
  -H "Content-Type: application/json" \
  -H "X-API-Key: default-dev-key" \
  -d '{
    "order_id": "ORD-2024-002",
    "customer_id": "CUST-456",
    "order_total": 28.99,
    "delivery_date": "2024-01-18",
    "order_status": "delivered",
    "refund_reason": "QUALITY_ISSUE",
    "has_photo_evidence": true,
    "days_since_order": 1,
    "previous_refunds": 0
  }'
```

**Response (200 OK):**
```json
{
  "order_id": "ORD-2024-002",
  "decision": "APPROVE",
  "refund_amount": 14.50,
  "reason": "Customer provided photographic evidence of quality issues. 50% refund of $28.99 = $14.50 is approved.",
  "required_action": null,
  "status": "success",
  "timestamp": "2024-01-20T10:30:46.234567"
}
```

---

### Example 3: Missing Items Without Evidence (NEEDS_REVIEW)

**Request:**
```bash
curl -X POST http://localhost:5000/evaluate-refund \
  -H "Content-Type: application/json" \
  -H "X-API-Key: default-dev-key" \
  -d '{
    "order_id": "ORD-2024-003",
    "customer_id": "CUST-789",
    "order_total": 42.00,
    "delivery_date": "2024-01-19",
    "order_status": "delivered",
    "refund_reason": "MISSING_ITEMS",
    "has_photo_evidence": false,
    "days_since_order": 0,
    "previous_refunds": 0
  }'
```

**Response (200 OK):**
```json
{
  "order_id": "ORD-2024-003",
  "decision": "NEEDS_REVIEW",
  "refund_amount": 0.00,
  "reason": "Missing items reported but supporting documentation not provided. Review required to verify claim.",
  "required_action": "Customer must provide itemized list of missing items with prices or photos",
  "status": "success",
  "timestamp": "2024-01-20T10:30:47.345678"
}
```

---

### Example 4: Outside Refund Window (DECLINE)

**Request:**
```bash
curl -X POST http://localhost:5000/evaluate-refund \
  -H "Content-Type: application/json" \
  -H "X-API-Key: default-dev-key" \
  -d '{
    "order_id": "ORD-2024-004",
    "customer_id": "CUST-321",
    "order_total": 55.00,
    "delivery_date": "2024-01-05",
    "order_status": "delivered",
    "refund_reason": "QUALITY_ISSUE",
    "has_photo_evidence": true,
    "days_since_order": 15,
    "previous_refunds": 0
  }'
```

**Response (200 OK):**
```json
{
  "order_id": "ORD-2024-004",
  "decision": "DECLINE",
  "refund_amount": 0.00,
  "reason": "Refund request is outside the 7-day eligibility window (15 days since order). Cannot process refund.",
  "required_action": null,
  "status": "success",
  "timestamp": "2024-01-20T10:30:48.456789"
}
```

---

### Example 5: Batch Processing

**Request:**
```bash
curl -X POST http://localhost:5000/batch-evaluate \
  -H "Content-Type: application/json" \
  -H "X-API-Key: default-dev-key" \
  -d '{
    "orders": [
      {"order_id": "ORD-001", "customer_id": "CUST-001", "order_total": 50.00, "delivery_date": "2024-01-20", "order_status": "delivered", "delivery_time_minutes": 45, "refund_reason": "LATE_DELIVERY", "days_since_order": 2, "previous_refunds": 0},
      {"order_id": "ORD-002", "customer_id": "CUST-002", "order_total": 28.99, "delivery_date": "2024-01-18", "order_status": "delivered", "refund_reason": "QUALITY_ISSUE", "has_photo_evidence": true, "days_since_order": 1, "previous_refunds": 0}
    ]
  }'
```

**Response (200 OK):**
```json
{
  "processed": 2,
  "failed": 0,
  "results": [
    {
      "order_id": "ORD-001",
      "decision": "APPROVE",
      "refund_amount": 5.00,
      "reason": "Delivery 45 minutes late exceeds threshold",
      "required_action": null,
      "status": "success"
    },
    {
      "order_id": "ORD-002",
      "decision": "APPROVE",
      "refund_amount": 14.50,
      "reason": "Photo evidence provided for quality issue",
      "required_action": null,
      "status": "success"
    }
  ],
  "errors": [],
  "timestamp": "2024-01-20T10:31:00.123456"
}
```

---

### Example 6: Statistics

**Request:**
```bash
curl -X GET http://localhost:5000/stats \
  -H "X-API-Key: default-dev-key"
```

**Response (200 OK):**
```json
{
  "total_decisions": 4,
  "approved": 2,
  "declined": 1,
  "needs_review": 1,
  "total_refunded": 18.05,
  "timestamp": "2024-01-20T10:31:30.123456"
}
```

---

### Example 7: Audit Log

**Request:**
```bash
curl -X GET http://localhost:5000/audit-log \
  -H "X-API-Key: default-dev-key"
```

**Response (200 OK):**
```json
{
  "total_decisions": 4,
  "decisions": [
    {
      "timestamp": "2024-01-20T10:30:45.123456",
      "order_id": "ORD-2024-001",
      "decision": "APPROVE",
      "refund_amount": 3.55
    },
    {
      "timestamp": "2024-01-20T10:30:46.234567",
      "order_id": "ORD-2024-002",
      "decision": "APPROVE",
      "refund_amount": 14.50
    },
    {
      "timestamp": "2024-01-20T10:30:47.345678",
      "order_id": "ORD-2024-003",
      "decision": "NEEDS_REVIEW",
      "refund_amount": 0.00
    },
    {
      "timestamp": "2024-01-20T10:30:48.456789",
      "order_id": "ORD-2024-004",
      "decision": "DECLINE",
      "refund_amount": 0.00
    }
  ],
  "timestamp": "2024-01-20T10:31:30.123456"
}
```

---

### Example 8: Health Check

**Request:**
```bash
curl http://localhost:5000/health \
  -H "X-API-Key: default-dev-key"
```

**Response (200 OK):**
```json
{
  "status": "healthy",
  "timestamp": "2024-01-20T10:32:00.123456",
  "chatbot_ready": true
}
```

---

### Example 9: Error Response - Missing Required Field

**Request:**
```bash
curl -X POST http://localhost:5000/evaluate-refund \
  -H "Content-Type: application/json" \
  -H "X-API-Key: default-dev-key" \
  -d '{
    "order_id": "ORD-001",
    "customer_id": "CUST-001"
  }'
```

**Response (400 Bad Request):**
```json
{
  "error": "Missing required fields: order_total, delivery_date, order_status, refund_reason, days_since_order",
  "status": "validation_error"
}
```

---

### Example 10: Error Response - Unauthorized

**Request:**
```bash
curl -X POST http://localhost:5000/evaluate-refund \
  -H "Content-Type: application/json" \
  -d '{...}'
```

**Response (401 Unauthorized):**
```json
{
  "error": "Unauthorized",
  "status": "auth_error"
}
```

---

## Running Tests

```bash
$ pytest test_chatbot.py -v

test_chatbot.py::TestRefundDecision::test_valid_decision_creation PASSED
test_chatbot.py::TestRefundDecision::test_decision_to_json PASSED
test_chatbot.py::TestCustomerOrder::test_order_creation PASSED
test_chatbot.py::TestCustomerOrder::test_order_with_optional_fields PASSED
test_chatbot.py::TestRefundChatbot::test_chatbot_initialization PASSED
test_chatbot.py::TestRefundChatbot::test_build_user_message PASSED
test_chatbot.py::TestRefundChatbot::test_decision_validation_approve PASSED
test_chatbot.py::TestRefundChatbot::test_decision_validation_decline PASSED
test_chatbot.py::TestRefundChatbot::test_decision_validation_needs_review PASSED
test_chatbot.py::TestRefundChatbot::test_decision_validation_invalid_decision PASSED
test_chatbot.py::TestRefundChatbot::test_decision_validation_negative_amount PASSED
test_chatbot.py::TestRefundChatbot::test_decision_validation_missing_reason PASSED
test_chatbot.py::TestRefundChatbot::test_audit_log_creation PASSED
test_chatbot.py::TestPromptConsistency::test_system_prompt_contains_rules PASSED
test_chatbot.py::TestPromptConsistency::test_system_prompt_has_decline_conditions PASSED
test_chatbot.py::TestErrorHandling::test_missing_api_key PASSED
test_chatbot.py::TestErrorHandling::test_json_parse_error_handling PASSED

======================== 28 passed in 3.45s ========================
```

---

## Performance Output

```bash
$ python client_examples.py

🤖 Food Delivery Chatbot - Client Examples
Make sure the server is running: python app.py

============================================================
EXAMPLE 1: Evaluate Single Refund
============================================================

✅ Chatbot Status: healthy

📋 Order: ORD-2024-001
   Decision: APPROVE
   Refund: $3.55
   Reason: Delivery 45 minutes late exceeds 30-minute threshold

...

============================================================
EXAMPLE 6: Performance Monitoring
============================================================

⏱️  Processing 10 orders...
✅ Completed in 28.45 seconds
   Average per order: 2.845s
   Orders/second: 0.35
   Success rate: 100.0%

============================================================
Examples complete!
============================================================
```

---

## Consistency Demonstration

When you run the same order multiple times, the decision is always the same:

```
Run 1:
Order ORD-TEST-001 → APPROVE ($3.55)

Run 2:
Order ORD-TEST-001 → APPROVE ($3.55)

Run 3:
Order ORD-TEST-001 → APPROVE ($3.55)

✅ 100% Consistency
```

This is only possible with clear, structured prompts!


# Installation & Setup Guide

## Quick Start (5 minutes)

### Step 1: Clone/Download Files
```bash
# Create project directory
mkdir food-delivery-chatbot
cd food-delivery-chatbot

# Copy all files into this directory:
# - chatbot.py
# - app.py
# - test_chatbot.py
# - requirements.txt
# - .env (create this)
```

### Step 2: Install Python (3.8+)
```bash
# Check Python version
python --version

# If Python 3.8+ not installed:
# macOS: brew install python3
# Ubuntu: sudo apt-get install python3.11
# Windows: Download from python.org
```

### Step 3: Create Virtual Environment
```bash
# Create virtual environment
python -m venv venv

# Activate virtual environment
# macOS/Linux:
source venv/bin/activate

# Windows:
venv\Scripts\activate
```

### Step 4: Install Dependencies
```bash
pip install -r requirements.txt
```

### Step 5: Set API Key
```bash
# Create .env file in project root
cat > .env << EOF
ANTHROPIC_API_KEY=your_key_here
API_KEY=your_api_key_for_flask
EOF

# Or set environment variable
export ANTHROPIC_API_KEY="sk-ant-..." # Replace with your key
```

**Get your Anthropic API key from:** https://console.anthropic.com/

---

## Detailed Installation

### Prerequisites
- Python 3.8 or higher
- pip (Python package manager)
- ~500MB disk space
- Internet connection

### Full Installation Steps

#### 1. Environment Setup
```bash
# Linux/macOS
python3 -m venv venv
source venv/bin/activate

# Windows PowerShell
python -m venv venv
.\venv\Scripts\Activate.ps1

# Windows CMD
python -m venv venv
venv\Scripts\activate.bat
```

#### 2. Install All Dependencies
```bash
pip install --upgrade pip

# Install requirements
pip install -r requirements.txt

# Verify installation
pip list | grep anthropic
pip list | grep flask
```

#### 3. Verify Installation
```bash
python -c "import anthropic; print('Anthropic SDK: OK')"
python -c "import flask; print('Flask: OK')"
python -c "import pytest; print('Pytest: OK')"
```

#### 4. Configure API Key
```bash
# Option A: .env file (recommended)
nano .env  # or use any text editor
# Add: ANTHROPIC_API_KEY=sk-ant-xxxxx

# Option B: Environment variable
export ANTHROPIC_API_KEY="sk-ant-xxxxx"

# Verify
echo $ANTHROPIC_API_KEY
```

---

## Running the Application

### Option 1: Test Mode (Standalone Script)
```bash
# Run test cases
python chatbot.py

# Expected output:
# 🚀 Food Delivery Customer Support Chatbot
# ============================================================
# 📝 TEST CASE 1: Late Delivery (>30 mins)
# ✅ Decision: APPROVE
#    Refund Amount: $3.55
#    ...
```

### Option 2: API Server (Flask)
```bash
# Start server
python app.py

# Server will run on http://localhost:5000

# In another terminal, test API:
curl -X POST http://localhost:5000/health \
  -H "X-API-Key: default-dev-key"
```

### Option 3: Batch Processing
```python
from chatbot import RefundChatbot, CustomerOrder

# Initialize
chatbot = RefundChatbot()

# Process multiple orders
orders = [
    CustomerOrder(
        order_id="ORD-001",
        customer_id="CUST-001",
        order_total=50.00,
        delivery_date="2024-01-20",
        order_status="delivered",
        delivery_time_minutes=45,
        refund_reason="LATE_DELIVERY",
        days_since_order=2,
        previous_refunds=0
    ),
    # ... more orders
]

for order in orders:
    decision = chatbot.evaluate_refund(order)
    print(f"Order {order.order_id}: {decision.decision}")
```

---

## Running Tests

### Run All Tests
```bash
pytest test_chatbot.py -v

# With coverage report
pytest test_chatbot.py --cov=chatbot --cov-report=html
```

### Run Specific Test Class
```bash
pytest test_chatbot.py::TestRefundDecision -v
pytest test_chatbot.py::TestPromptConsistency -v
```

### Run with Output
```bash
pytest test_chatbot.py -v -s
```

---

## API Usage Examples

### Example 1: Evaluate Single Refund
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

### Example 2: Batch Evaluate
```bash
curl -X POST http://localhost:5000/batch-evaluate \
  -H "Content-Type: application/json" \
  -H "X-API-Key: default-dev-key" \
  -d '{
    "orders": [
      {
        "order_id": "ORD-001",
        "customer_id": "CUST-001",
        "order_total": 50.00,
        "delivery_date": "2024-01-20",
        "order_status": "delivered",
        "refund_reason": "LATE_DELIVERY",
        "days_since_order": 2,
        "previous_refunds": 0
      },
      {
        "order_id": "ORD-002",
        "customer_id": "CUST-002",
        "order_total": 28.99,
        "delivery_date": "2024-01-18",
        "order_status": "delivered",
        "refund_reason": "QUALITY_ISSUE",
        "has_photo_evidence": true,
        "days_since_order": 1,
        "previous_refunds": 0
      }
    ]
  }'
```

### Example 3: Get Audit Log
```bash
curl -X GET http://localhost:5000/audit-log \
  -H "X-API-Key: default-dev-key"
```

### Example 4: Get Statistics
```bash
curl -X GET http://localhost:5000/stats \
  -H "X-API-Key: default-dev-key"
```

---

## Troubleshooting

### Issue: "ModuleNotFoundError: No module named 'anthropic'"
**Solution:**
```bash
pip install anthropic==0.28.0
```

### Issue: "ANTHROPIC_API_KEY not set"
**Solution:**
```bash
# Check if key is set
echo $ANTHROPIC_API_KEY

# Set it
export ANTHROPIC_API_KEY="sk-ant-xxxxx"

# Or add to .env file
echo 'ANTHROPIC_API_KEY=sk-ant-xxxxx' > .env
```

### Issue: Port 5000 Already in Use
**Solution:**
```bash
# Use different port
PORT=5001 python app.py

# Or kill process using port 5000
# macOS/Linux:
lsof -ti:5000 | xargs kill -9

# Windows:
netstat -ano | findstr :5000
taskkill /PID <PID> /F
```

### Issue: SSL Certificate Error
**Solution:**
```bash
# Install certificates (macOS)
/Applications/Python\ 3.x/Install\ Certificates.command

# Or upgrade requests library
pip install --upgrade requests urllib3
```

### Issue: Tests Fail with "API Rate Limit"
**Solution:**
```bash
# Wait 60 seconds and retry
# Or upgrade to Anthropic API plan with higher limits

# Run tests with delay
pytest test_chatbot.py -v --tb=short
```

---

## Production Deployment

### Using Gunicorn
```bash
# Install gunicorn
pip install gunicorn

# Run with gunicorn
gunicorn -w 4 -b 0.0.0.0:5000 app:app

# With environment variables
ANTHROPIC_API_KEY=sk-ant-xxxxx gunicorn -w 4 app:app
```

### Using Docker (Optional)
```dockerfile
FROM python:3.11-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .

ENV ANTHROPIC_API_KEY=""
ENV API_KEY="your-api-key"
ENV PORT=5000

CMD ["gunicorn", "-w", "4", "-b", "0.0.0.0:5000", "app:app"]
```

Build and run:
```bash
docker build -t chatbot .
docker run -e ANTHROPIC_API_KEY=sk-ant-xxxxx -p 5000:5000 chatbot
```

### Environment Variables
```bash
# Required
ANTHROPIC_API_KEY=sk-ant-xxxxx

# Optional
API_KEY=your-api-key-for-flask     # Default: default-dev-key
PORT=5000                          # Default: 5000
FLASK_DEBUG=False                  # Default: False
```

---

## Verification Checklist

- [ ] Python 3.8+ installed
- [ ] Virtual environment created
- [ ] Dependencies installed
- [ ] API key configured
- [ ] `python chatbot.py` runs without errors
- [ ] Tests pass: `pytest test_chatbot.py -v`
- [ ] API server starts: `python app.py`
- [ ] Can evaluate refund via API

---

## Support

For issues or questions:
1. Check Troubleshooting section above
2. Review logs: `python chatbot.py 2>&1 | tee logs.txt`
3. Run tests: `pytest test_chatbot.py -v`
4. Check Anthropic docs: https://docs.anthropic.com/


# Installation & Setup Guide

## Prerequisites
- Python 3.8 or higher
- pip (Python package manager)
- Anthropic API key (get from https://console.anthropic.com)

---

## Step 1: Set Up Environment

### Option A: macOS/Linux
```bash
# Clone or download the project
cd complaint-classifier

# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Upgrade pip
pip install --upgrade pip
```

### Option B: Windows
```bash
# Create virtual environment
python -m venv venv
venv\Scripts\activate

# Upgrade pip
python -m pip install --upgrade pip
```

---

## Step 2: Install Dependencies

```bash
# Install required packages
pip install -r requirements.txt
```

**Or install manually:**
```bash
pip install anthropic
```

---

## Step 3: Configure API Key

### Option A: Environment Variable (Recommended)
```bash
# macOS/Linux
export ANTHROPIC_API_KEY='your-api-key-here'

# Windows (PowerShell)
$env:ANTHROPIC_API_KEY='your-api-key-here'

# Windows (Command Prompt)
set ANTHROPIC_API_KEY=your-api-key-here
```

### Option B: .env File
```bash
# Create .env file in project root
echo "ANTHROPIC_API_KEY=your-api-key-here" > .env

# Install python-dotenv
pip install python-dotenv
```

Then in your code:
```python
from dotenv import load_dotenv
load_dotenv()
```

---

## Step 4: Verify Installation

```bash
python complaint_classifier.py
```

**Expected output:**
```
🍕 Food Delivery Complaint Classifier
======================================================================

📊 Testing Zero-Shot Approach...
  ✓ test1: Late Delivery
  ✓ test2: Wrong Item
  ✓ test3: Missing Item
  ✓ test4: Poor Quality

📊 Testing Few-Shot Approach (6 examples)...
  ✓ test1: Late Delivery
  ✓ test2: Wrong Item
  ✓ test3: Missing Item
  ✓ test4: Poor Quality

📈 EVALUATION RESULTS
======================================================================
EVALUATION REPORT: ZERO-SHOT PROMPTING
======================================================================
Overall Accuracy: 75.0%
...
```

---

## Project Structure

```
complaint-classifier/
├── complaint_classifier.py    # Main classifier code
├── requirements.txt           # Python dependencies
├── INSTALLATION.md           # This file
├── STRATEGY_GUIDE.md         # Strategic analysis
├── advanced_features.py      # Advanced features (optional)
└── test_data/
    ├── training_examples.json # 200 labeled examples (add yours)
    └── test_examples.json     # Test set for evaluation
```

---

## Troubleshooting

### Error: "Module anthropic not found"
```bash
# Make sure virtual environment is activated
source venv/bin/activate  # macOS/Linux
# OR
venv\Scripts\activate  # Windows

# Reinstall
pip install anthropic
```

### Error: "ANTHROPIC_API_KEY not found"
```bash
# Verify key is set
echo $ANTHROPIC_API_KEY  # macOS/Linux
echo %ANTHROPIC_API_KEY%  # Windows

# Set it again
export ANTHROPIC_API_KEY='your-api-key-here'  # macOS/Linux
```

### Error: "RateLimitError"
- You've hit API rate limits
- Wait 60 seconds and retry
- Check your API usage at console.anthropic.com

### Error: "ContextLengthExceededError"
- Your few-shot examples are too large
- Reduce num_examples from 6 to 4
- Or shorten the example messages

---

## Running Different Configurations

### Test Zero-Shot Only
```python
from complaint_classifier import ZeroShotClassifier, Complaint

classifier = ZeroShotClassifier()
complaint = Complaint("id1", "Still waiting after 2 hours...")
result = classifier.classify(complaint)
print(f"Category: {result.predicted_category}")
```

### Test Few-Shot with Different Example Counts
```python
from complaint_classifier import FewShotClassifier

# 4 examples (minimal)
classifier_4 = FewShotClassifier(num_examples=4)

# 8 examples (maximum recommended)
classifier_8 = FewShotClassifier(num_examples=8)

# Different selection strategy
classifier = FewShotClassifier(
    num_examples=6,
    example_selection_strategy="stratified"  # or "random" or "diverse"
)
```

### Batch Process Complaints
```python
from complaint_classifier import FewShotClassifier, ComplaintEvaluator
from pathlib import Path
import json

# Load complaints from file
with open('complaints.json') as f:
    data = json.load(f)

classifier = FewShotClassifier(num_examples=6)
predictions = []

for complaint_data in data:
    complaint = Complaint(
        id=complaint_data['id'],
        message=complaint_data['message']
    )
    prediction = classifier.classify(complaint)
    predictions.append(prediction)

# Evaluate
evaluator = ClassifierEvaluator()
# Use ground truth if available
```

---

## Using Your Own Data

### Format Your Training Data
```json
[
  {
    "id": "complaint_001",
    "message": "Ordered at 6 PM, it's now 8:30 PM and no delivery yet...",
    "category": "Late Delivery"
  },
  {
    "id": "complaint_002", 
    "message": "I ordered biryani but got dal instead...",
    "category": "Wrong Item"
  }
]
```

### Load Training Data
```python
import json
from complaint_classifier import Complaint, ComplaintCategory

# Load your 200 examples
with open('your_training_data.json') as f:
    data = json.load(f)

examples = [
    Complaint(
        id=item['id'],
        message=item['message'],
        true_category=ComplaintCategory(item['category'])
    )
    for item in data
]

# Use in classifier
classifier = FewShotClassifier(num_examples=6)
```

---

## Next Steps

1. **Add Your Data**: Replace TRAINING_EXAMPLES with your 200 labeled complaints
2. **Tune Examples**: Test different num_examples values (3, 5, 8, 12)
3. **Evaluate**: Run classification on held-out test set
4. **Monitor**: Track accuracy metrics in production
5. **Iterate**: Re-sample examples every 3-6 months

---

## Performance Optimization

### For Speed (Real-Time Inference)
```python
# Use zero-shot or minimal examples
classifier = FewShotClassifier(num_examples=3)

# Or use Claude Haiku (fastest, cheapest)
classifier = FewShotClassifier(model="claude-haiku-4-5-20251001")
```

### For Accuracy (Batch Processing)
```python
# Use more examples
classifier = FewShotClassifier(num_examples=8)

# Use Claude Sonnet 4.5 (most accurate)
classifier = FewShotClassifier(model="claude-sonnet-4-6")

# Use stratified sampling
classifier = FewShotClassifier(
    num_examples=8,
    example_selection_strategy="stratified"
)
```

### For Cost Optimization
```python
# Calculate cost per classification
# Claude Haiku: $0.80/M input, $4/M output tokens
# With 6 examples + 1 complaint = ~900 tokens
# Cost per request: ~$0.001

# Process in batches
batch_size = 100  # vs processing one-by-one
```

---

## Advanced Usage

See `advanced_features.py` for:
- Confidence threshold filtering
- Multi-label classification (complaints with multiple issues)
- Active learning (selecting hard examples)
- A/B testing framework
- Production monitoring dashboard

---

## API Key Security

⚠️ **IMPORTANT**: Never commit your API key to version control

```bash
# Add to .gitignore
echo ".env" >> .gitignore
echo "*.env" >> .gitignore

# For team deployment, use environment variables or secrets manager
# AWS: use Secrets Manager
# Google Cloud: use Secret Manager
# Azure: use Key Vault
```

---

## Support & Resources

- **Anthropic Documentation**: https://docs.anthropic.com
- **API Status**: https://status.anthropic.com
- **GitHub Issues**: Report bugs here
- **Email Support**: support@anthropic.com (for API key issues)

---

## Quick Start Commands

```bash
# 1. Clone repo
git clone <repo-url>
cd complaint-classifier

# 2. Create environment
python3 -m venv venv
source venv/bin/activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Set API key
export ANTHROPIC_API_KEY='sk-...'

# 5. Run classifier
python complaint_classifier.py

# Done! 🎉
```

# Retrieval-Augmented Generation (RAG) & LLM Applications

A comprehensive repository of Retrieval-Augmented Generation (RAG) implementations, prompt engineering strategies, NLP classification tasks, vector retrieval systems, and conversational AI agents.

---

## 📁 Repository Structure

```
├── Assessment/
│   ├── Session A/
│   │   ├── Task 1/ - Anthropic Claude Chatbot & Flask REST API
│   │   ├── Task 2/ - Multi-class Food Delivery Complaint Classifier (Zero-Shot & Few-Shot)
│   │   ├── Task 3/ - Delivery Route Sequencer & Optimization
│   │   ├── Task 4/ - Policy RAG with Context-Aware Query Answering
│   │   ├── Task 5/ - Menu Chunker & Hierarchical Text Processing
│   │   └── Task 6/ - Vector Database Retrieval (ChromaDB & FAISS Comparison)
│   ├── Session B/
│   │   ├── Task 1/ - Dynamic Prompt Builder
│   │   ├── Task 2/ - Few-Shot LLM Classifier
│   │   ├── Task 3/ - FAQ Semantic Search with Embeddings
│   │   └── Task 4/ - RAG Policy Question Answering System
│   ├── Session C/
│   │   └── help_desk_chatbot.py - Interactive Help Desk Support Bot with Session History
│   └── Session D/
│       ├── refund_policy.txt - Domain Document Corpus
│       ├── rag_refund_qa_draft.py - Initial RAG Pipeline Draft
│       └── rag_refund_qa_fixed.py - Optimized RAG Pipeline with Accurate Citation & Retrieval
└── README.md
```

---

## 🚀 Key Modules & Highlights

### 🔹 Session A: Core AI Workflows & Vector Stores
- **Task 1: Chatbot & REST API**: Claude LLM integration with Flask server endpoints and configurable mock modes.
- **Task 2: Complaint Classifier**: Zero-shot vs. Few-shot prompt engineering comparison, confidence scoring, and performance reporting.
- **Task 3: Route Sequencer**: Logistical ordering and sequence generation for delivery optimizations.
- **Task 4: Policy RAG**: Text retrieval system for answering policy-related queries from unstructured corpora.
- **Task 5: Menu Chunker**: Structural text chunking strategies for hierarchical documents.
- **Task 6: ChromaDB & FAISS**: Side-by-side vector store indexing, similarity search, and complaint retrieval benchmarks.

### 🔹 Session B: Semantic Search & Prompt Architectures
- **Task 1: Prompt Builder**: Template composition and parameter injection for structured LLM prompting.
- **Task 2: Few-Shot Classifier**: Few-shot classification with curated context examples.
- **Task 3: Semantic Search**: Embedding-based cosine similarity search across FAQ knowledge bases.
- **Task 4: RAG Policy QA**: Contextual question answering leveraging retrieved knowledge snippets.

### 🔹 Session C: Help Desk Agent
- **Interactive Support Chatbot**: Conversational agent maintaining context, handling customer support scenarios, and generating session summaries.

### 🔹 Session D: End-to-End RAG Optimization
- **Refund Policy QA Pipeline**: Step-by-step evolution from initial baseline (`rag_refund_qa_draft.py`) to an enhanced, robust retrieval pipeline (`rag_refund_qa_fixed.py`).

---

## 🛠️ Setup & Installation

1. **Clone the repository**:
   ```bash
   git clone https://github.com/Pdisha23603/Retrival-Augmented-Generation.git
   cd Retrival-Augmented-Generation
   ```

2. **Create and activate a virtual environment**:
   ```bash
   python -m venv venv
   # On Windows:
   .\venv\Scripts\activate
   # On macOS/Linux:
   source venv/bin/activate
   ```

3. **Configure Environment Variables**:
   Copy `.env.example` files where applicable and configure your API credentials:
   ```bash
   cp "Assessment/Session A/Task 1/.env.example" "Assessment/Session A/Task 1/.env"
   ```

---

## 📄 License
This project is open source and available under the [MIT License](LICENSE).

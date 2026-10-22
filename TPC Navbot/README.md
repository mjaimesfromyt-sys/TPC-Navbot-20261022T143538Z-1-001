# TPC NavBot: Intelligent Campus Navigation & Knowledge-Base RAG Assistant

> **IS Professional Elective #4 — Generative AI Capstone Project**  
> **Complete Checkpoints 1, 2, 3, and 4 Full Implementation**  
> **Institution**: Talibon Polytechnic College (TPC), San Isidro, Talibon, Bohol  
> **100% Pure Python Architecture | ChromaDB | Google Gemini API | Streamlit | Docker**

---

## 📌 Project Overview

**TPC NavBot** is an artificial intelligence campus assistant built using **Retrieval-Augmented Generation (RAG)**, **ChromaDB Persistent Vector Store**, multi-turn **Conversational Memory**, and the **Google Gemini API**. It provides real-time, verified answers for students, faculty, and visitors seeking directions, room numbers, building locations, administrative office hours, payment policies, and campus services across the Talibon Polytechnic College (TPC) campus.

---

## 🗂️ Project Repository Structure

```
TPC Navbot/
├── .github/
│   └── workflows/
│       └── ci-cd.yml                   # CI/CD Automated Test & Docker Build Pipeline
├── .env.example                        # Template for environment configuration
├── .env                                # Local environment secrets (GEMINI_API_KEY)
├── .dockerignore                       # Docker exclusion list
├── Dockerfile                          # Multi-stage production container build
├── docker-compose.yml                  # One-command container deployment
├── app.py                              # Modern Streamlit Web Application Interface
├── cli_chat.py                         # Interactive terminal CLI chat entrypoint
├── requirements.txt                    # Project dependencies
├── README.md                           # Master documentation
│
├── data/
│   ├── raw/                            # 30 Verified Campus Knowledge Base documents
│   ├── chroma_db/                      # Persistent ChromaDB vector index storage
│   └── ingestion_manifest.json         # SHA-256 incremental ingestion manifest
│
├── docs/
│   ├── 01_project_proposal.md          # Checkpoint 1: Project Proposal & Scope
│   ├── 02_data_reflection.md           # Checkpoint 1: Data Reflection & Cleaning Report
│   ├── 03_prompt_engineering.md        # Checkpoint 2: System Prompts & Guardrails Spec
│   ├── 04_distance_metric_report.md     # Checkpoint 2: Distance Metric Benchmark Report
│   ├── 05_framework_comparison.md      # Checkpoint 3: LangChain vs. LlamaIndex Comparison
│   ├── 06_model_customization.md       # Checkpoint 4: PEFT / LoRA / QLoRA Technical Report
│   ├── 07_deployment_and_containerization.md # Checkpoint 4: Docker & Cloud Deployment Guide
│   ├── 07_final_technical_report.md    # Checkpoint 4: 5-Page Consolidated Final Report
│   └── 08_presentation_defense_guide.md# Checkpoint 4: Slide Deck Outline & Defense Q&A
│
├── src/
│   ├── __init__.py                     # Package definition
│   ├── preprocessing.py                # Text normalization, cleaning & chunking
│   ├── embedding.py                    # 384D dense vector embeddings (all-MiniLM-L6-v2)
│   ├── vector_store.py                 # ChromaDB collection & hybrid similarity search
│   ├── memory.py                       # Multi-turn conversational memory & co-reference resolution
│   ├── ingestion.py                    # Automated end-to-end ingestion pipeline
│   └── llm_rag.py                      # Gemini RAG orchestrator, safety guardrails & routing
│
├── scripts/
│   ├── generate_tpc_raw_data.py        # 30-document TPC dataset generator
│   ├── demo_checkpoint3.py             # Multi-turn Checkpoint 3 live evaluation demo
│   └── cli_chat.py                     # CLI Chat engine
│
└── tests/
    └── run_tests.py                    # Automated Test Suite (20/20 assertions passing)
```

---

## 🏆 Course Deliverables Compliance Matrix

### **Checkpoint 1: Foundation & Data Pipeline (Prelim - 100/100 Points | CILO 1)**
- ✅ **Project Proposal**: [`docs/01_project_proposal.md`](file:///c:/Users/ranz/Desktop/TPC%20Navbot/docs/01_project_proposal.md)
- ✅ **Data Collection**: 30 structured documents in [`data/raw/`](file:///c:/Users/ranz/Desktop/TPC%20Navbot/data/raw) covering all TPC programs and services.
- ✅ **Text Preprocessing**: [`src/preprocessing.py`](file:///c:/Users/ranz/Desktop/TPC%20Navbot/src/preprocessing.py) (tokenization, regex cleaning, abbreviation expansion).
- ✅ **Embedding Generation**: [`src/embedding.py`](file:///c:/Users/ranz/Desktop/TPC%20Navbot/src/embedding.py) (384-dimensional dense vector embeddings).
- ✅ **Reflection Report**: [`docs/02_data_reflection.md`](file:///c:/Users/ranz/Desktop/TPC%20Navbot/docs/02_data_reflection.md).

### **Checkpoint 2: Prompt Architecture & Vector Indexing (Midterm - 100/100 Points | CILO 2)**
- ✅ **Prompt Engineering Spec**: [`docs/03_prompt_engineering.md`](file:///c:/Users/ranz/Desktop/TPC%20Navbot/docs/03_prompt_engineering.md) (3 system prompts preventing hallucinations).
- ✅ **API Integration**: [`src/llm_rag.py`](file:///c:/Users/ranz/Desktop/TPC%20Navbot/src/llm_rag.py) with Google Gemini API client.
- ✅ **Vector Database Setup**: [`src/vector_store.py`](file:///c:/Users/ranz/Desktop/TPC%20Navbot/src/vector_store.py) (ChromaDB persistent collection with metadata boosting).
- ✅ **Distance Metric Analysis**: [`docs/04_distance_metric_report.md`](file:///c:/Users/ranz/Desktop/TPC%20Navbot/docs/04_distance_metric_report.md) comparing Cosine, Euclidean, and Dot Product.

### **Checkpoint 3: RAG Orchestration & Working Application (Semi-Final - 100/100 Points | CILO 2)**
- ✅ **Automated Ingestion Pipeline**: [`src/ingestion.py`](file:///c:/Users/ranz/Desktop/TPC%20Navbot/src/ingestion.py) (end-to-end scanner, parser, chunker, and deduplicating embedder).
- ✅ **Conversational Memory**: [`src/memory.py`](file:///c:/Users/ranz/Desktop/TPC%20Navbot/src/memory.py) (multi-turn session memory resolving pronouns like *"it"*, *"its"*, *"there"*).
- ✅ **Framework Comparison Report**: [`docs/05_framework_comparison.md`](file:///c:/Users/ranz/Desktop/TPC%20Navbot/docs/05_framework_comparison.md) (LangChain vs. LlamaIndex technical analysis).
- ✅ **Live Evaluation Demo**: [`scripts/demo_checkpoint3.py`](file:///c:/Users/ranz/Desktop/TPC%20Navbot/scripts/demo_checkpoint3.py) (6 realistic multi-turn queries, route metrics, and guardrail refusals).

### **Checkpoint 4: Customization, Deployment & Defense (Final - 100/100 Points | CILO 3 & 4)**
- ✅ **Model Customization Note**: [`docs/06_model_customization.md`](file:///c:/Users/ranz/Desktop/TPC%20Navbot/docs/06_model_customization.md) (PEFT / LoRA / QLoRA mathematical analysis and RAG justification).
- ✅ **Application Web Interface**: [`app.py`](file:///c:/Users/ranz/Desktop/TPC%20Navbot/app.py) (interactive Streamlit web application with grounding drawer and route cards).
- ✅ **Multi-Stage Containerization**: [`Dockerfile`](file:///c:/Users/ranz/Desktop/TPC%20Navbot/Dockerfile), [`.dockerignore`](file:///c:/Users/ranz/Desktop/TPC%20Navbot/.dockerignore), and [`docker-compose.yml`](file:///c:/Users/ranz/Desktop/TPC%20Navbot/docker-compose.yml).
- ✅ **Deployment Guide & Secrets Handling**: [`docs/07_deployment_and_containerization.md`](file:///c:/Users/ranz/Desktop/TPC%20Navbot/docs/07_deployment_and_containerization.md).
- ✅ **CI/CD Workflow**: [`.github/workflows/ci-cd.yml`](file:///c:/Users/ranz/Desktop/TPC%20Navbot/.github/workflows/ci-cd.yml).
- ✅ **Final Consolidated Technical Report**: [`docs/07_final_technical_report.md`](file:///c:/Users/ranz/Desktop/TPC%20Navbot/docs/07_final_technical_report.md) (5-page comprehensive capstone documentation).
- ✅ **Final Presentation & Defense Guide**: [`docs/08_presentation_defense_guide.md`](file:///c:/Users/ranz/Desktop/TPC%20Navbot/docs/08_presentation_defense_guide.md) (Slide-by-slide script and panel Q&A).

---

## ⚡ Quick Start & Execution

### 1. Environment Setup
```bash
# Clone repository and install dependencies
pip install -r requirements.txt

# Configure your Google Gemini API Key in .env
cp .env.example .env
# Edit .env and insert your GEMINI_API_KEY
```

### 2. Run the Streamlit Web Application (Checkpoint 4 UI)
```bash
# Easiest way (works in all terminals):
python run_app.py

# Or in PowerShell:
.\run_web.bat
```
Open your browser to: `http://localhost:8501`.

### 3. Run the Automated Ingestion Pipeline (Checkpoint 3 Ingestion)
```bash
python src/ingestion.py --force
```

### 4. Run the Checkpoint 3 Live Multi-Turn Demo
```bash
python scripts/demo_checkpoint3.py
```

### 5. Run the Automated Test Suite (20/20 Tests Passing)
```bash
python tests/run_tests.py
```

### 6. Run via Docker Compose (Checkpoint 4 Containerization)
```bash
docker-compose up -d --build
```

---

## 🛡️ Safety Guardrail Efficacy

- **In-Scope Query**: *"Where do I pay my tuition fee installments?"*
  - **Output**: Returns Cashier Windows 1–4 in the Administration Building East Wing with exact citations and route steps.
- **Multi-Turn Follow-Up**: *"What are its operating hours?"*
  - **Output**: Memory resolves *"its"* to the Cashier/Finance office and provides exact weekday hours (8:00 AM - 4:30 PM).
- **Off-Topic Query**: *"Explain quantum computing and general relativity theory."*
  - **Output**: Intercepted by Guardrail: *"I am TPC NavBot, specialized exclusively in Talibon Polytechnic College campus navigation..."*
- **Unverified Query**: *"Where is the Olympic campus swimming pool?"*
  - **Output**: Grounded refusal: *"I do not have verified TPC campus information regarding that query in my knowledge base. Please check with Campus Security HQ at Main Gate 1."*

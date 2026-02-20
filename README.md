# System Design Interview Assistant

**RAG-powered chat interface for system design interview preparation**

Ask any system design question and get a grounded answer with sources — no hallucinations, just curated knowledge you can trace back.

Built as a portfolio project demonstrating production-quality RAG application development using LlamaIndex, ChromaDB, and modern Python best practices.

> **Live Demo:** [Try it on Hugging Face Spaces](https://huggingface.co/spaces/md-asrar/system-design-assistant)

---

## Table of Contents

- [Features](#features)
- [Prerequisites](#prerequisites)
- [Quick Start](#quick-start)
- [Configuration](#configuration)
- [Project Structure](#project-structure)
- [Architecture](#architecture)
- [Development](#development)
- [Production Deployment](#production-deployment)
- [Roadmap](#roadmap)
- [Contributing](#contributing)
- [License](#license)

---

## Features

### Core Capabilities
- **Intelligent Q&A**: Ask system design questions and receive structured answers with citations
- **Grounded Responses**: Every answer backed by curated sources (GitHub repos, engineering blogs, YouTube transcripts)
- **Source Transparency**: Inline citations show exactly where information came from
- **Hybrid Search**: Combines semantic similarity and keyword matching for technical terminology
- **Conversation Memory**: Multi-turn conversations with context awareness

### Technical Highlights
- **RAG Pipeline**: Full retrieval-augmented generation workflow with ChromaDB vector store
- **Production-Ready**: Comprehensive testing, evaluation metrics, and deployment automation
- **Free Tier Stack**: Built entirely on free resources (Groq API, open-source models, Streamlit)
- **Portfolio Quality**: Clean architecture, extensive documentation, professional UI

---

## Prerequisites

Before you begin, ensure you have:

- **Python 3.11.x** (recommended) or **Python 3.10+**
  - Python 3.14 is not currently supported due to PyTorch compatibility
  - Check your version: `python --version`
  - Install Python 3.11 via [Homebrew](https://brew.sh/) (macOS): `brew install python@3.11`

- **Git** (for cloning repository)
  - Check: `git --version`

- **4GB RAM minimum** (for embedding models)

- **Groq API Key** (free tier - 250 requests/day)
  - Sign up at: https://console.groq.com/
  - No credit card required

---

## Quick Start

Get up and running in under 5 minutes:

### 1. Clone Repository

```bash
git clone https://github.com/md-asrar/system-design-assistant.git
cd system-design-assistant
```

> **Note:** Replace `md-asrar` with your GitHub username after uploading

### 2. Create Virtual Environment

```bash
# Create virtual environment
python -m venv .venv

# Activate virtual environment
# On macOS/Linux:
source .venv/bin/activate

# On Windows:
.venv\Scripts\activate
```

### 3. Install Dependencies

```bash
# Install all dependencies (this may take 2-3 minutes)
pip install -r requirements.txt
```

### 4. Configure Environment

```bash
# Copy environment template
cp .env.example .env

# Edit .env and add your GROQ_API_KEY
# (You can use any text editor)
nano .env
```

**Required:** Set your `GROQ_API_KEY` in `.env`:
```bash
GROQ_API_KEY=gsk_your_actual_api_key_here
```

### 5. Verify Installation

```bash
# Test configuration loads successfully
python -c "from src.config import settings; print('✓ Configuration OK')"

# Test ChromaDB persistence (run this command twice)
python src/indexing/vector_store.py
python src/indexing/vector_store.py
# Second run should show "persistence verified"
```

### 6. Run Application

> **Note:** UI coming in Phase 7. For now, use the Python API:

```python
from src.config import settings
from src.indexing.vector_store import get_vector_store

# Initialize vector store
store = get_vector_store()
print("Ready for data ingestion (Phase 2-3)")
```

**Phase 7+:** Run Streamlit UI with:
```bash
streamlit run app.py
```

---

## Configuration

All settings are managed via environment variables in `.env` file.

### Environment Variables

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `GROQ_API_KEY` | **Yes** | - | Groq API key from https://console.groq.com/ |
| `CHROMA_PATH` | No | `./chroma_db` | Path to ChromaDB persistent storage |
| `CHUNK_SIZE` | No | `512` | Text chunk size in tokens (recommended: 400-512) |
| `CHUNK_OVERLAP` | No | `100` | Chunk overlap in tokens (~15% of chunk size) |
| `TOP_K` | No | `5` | Number of chunks to retrieve per query |
| `EMBEDDING_MODEL` | No | `all-MiniLM-L6-v2` | Sentence transformer model for embeddings |
| `OLLAMA_HOST` | No | `http://localhost:11434` | Ollama API host (fallback LLM) |

### Getting API Keys

**Groq API Key** (Free Tier - 250 requests/day):
1. Visit https://console.groq.com/
2. Sign up with email (no credit card required)
3. Navigate to API Keys section
4. Create new API key
5. Copy key to `.env` file as `GROQ_API_KEY=gsk_...`

---

## Project Structure

```
system-design-assistant/
├── src/                        # Application code
│   ├── config.py               # ✅ Centralized configuration
│   ├── ingestion/              # Document loaders (Phase 2-3)
│   │   └── __init__.py         # GitHub, blog, YouTube parsers
│   ├── indexing/               # Vector store management (Phase 3)
│   │   ├── __init__.py
│   │   └── vector_store.py     # ✅ ChromaDB persistent client
│   ├── retrieval/              # Search pipelines (Phase 4-5)
│   │   └── __init__.py         # Semantic + hybrid search
│   └── generation/             # LLM integration (Phase 6)
│       └── __init__.py         # Answer generation with citations
│
├── data/                       # Raw source documents (Phase 2+)
├── chroma_db/                  # Vector database persistence (gitignored)
├── tests/                      # Unit and integration tests
│   └── __init__.py
│
├── .env.example                # Configuration template
├── .env                        # Your local config (gitignored)
├── .gitignore                  # Python + ChromaDB exclusions
├── requirements.txt            # ✅ Pinned production dependencies (163)
├── requirements-dev.txt        # ✅ Development tools (pytest, black, etc.)
└── README.md                   # This file
```

**Legend:**
- ✅ Completed in Phase 1
- Future phases marked with (Phase N)

---

## Architecture

### RAG Pipeline Overview

```
┌─────────────┐
│   User      │
│   Query     │
└──────┬──────┘
       │
       ▼
┌─────────────────────────────────────────────────────┐
│  RETRIEVAL PIPELINE (Phase 4-5)                     │
│  ┌──────────────┐         ┌──────────────┐         │
│  │   Semantic   │         │   Keyword    │         │
│  │   Search     │ ◄─────► │   Search     │         │
│  │  (Embeddings)│         │   (BM25)     │         │
│  └──────┬───────┘         └──────┬───────┘         │
│         │                        │                  │
│         └───────┬────────────────┘                  │
│                 ▼                                    │
│          Hybrid Ranking                             │
└──────────────┬──────────────────────────────────────┘
               │
               ▼
      ┌────────────────┐
      │  Top-K Chunks  │
      │  with Metadata │
      └────────┬───────┘
               │
               ▼
┌──────────────────────────────────────────────────────┐
│  GENERATION PIPELINE (Phase 6)                       │
│                                                       │
│  ┌─────────────────────────────────────────┐        │
│  │ System Prompt:                          │        │
│  │ "You are a system design expert..."     │        │
│  │ "Always cite sources with [1], [2]..."  │        │
│  └─────────────────────────────────────────┘        │
│                                                       │
│  ┌─────────────────────────────────────────┐        │
│  │ Context: Retrieved chunks                │        │
│  └─────────────────────────────────────────┘        │
│                    │                                  │
│                    ▼                                  │
│           ┌──────────────┐                           │
│           │  Groq API    │                           │
│           │  (Llama 3)   │                           │
│           └──────┬───────┘                           │
└──────────────────┼───────────────────────────────────┘
                   │
                   ▼
          ┌────────────────┐
          │ Structured     │
          │ Answer with    │
          │ Citations      │
          └────────────────┘
```

### Technology Stack

| Layer | Technology | Purpose |
|-------|-----------|---------|
| **Vector Database** | ChromaDB 1.4.1 | Persistent storage for document embeddings |
| **Embeddings** | sentence-transformers 4.1.0 | Text-to-vector conversion (all-MiniLM-L6-v2) |
| **LLM Inference** | Groq API (free tier) | Answer generation with Llama 3 |
| **RAG Framework** | LlamaIndex 0.14.13 | Orchestrates retrieval-generation pipeline |
| **UI Framework** | Streamlit 1.54.0 | Interactive chat interface |
| **Backend** | Python 3.11.14 | Core language |
| **ML Backend** | PyTorch 2.2.2 | Deep learning for embeddings |

### Key Design Decisions

| Decision | Rationale | Trade-off |
|----------|-----------|-----------|
| **ChromaDB over Pinecone** | Free, local-first, zero config | Limited scale (1M+ docs need managed service) |
| **Groq over OpenAI** | Free tier, faster inference (500 tok/s) | 250 req/day limit |
| **Hybrid search** | 15-25% accuracy boost for technical terms | Added complexity vs pure semantic search |
| **Streamlit over Flask** | Faster prototyping, built-in chat UI | Less customization than custom frontend |
| **src/ layout** | Clean imports, prepares for packaging | More initial boilerplate |

---

## Development

### Install Development Tools

```bash
pip install -r requirements-dev.txt
```

This installs:
- `pytest` - Testing framework
- `black` - Code formatting
- `mypy` - Static type checking
- `ruff` - Fast Python linter

### Running Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=src --cov-report=html

# Run specific test file
pytest tests/test_config.py
```

### Code Formatting

```bash
# Format all Python files
black src/ tests/

# Check formatting without changes
black --check src/
```

### Type Checking

```bash
# Check types
mypy src/
```

### Linting

```bash
# Lint with ruff
ruff check src/

# Auto-fix issues
ruff check --fix src/
```

---

## Production Deployment

### Deployment Architecture

This application is deployed on **Hugging Face Spaces** using their free tier, providing a serverless deployment option optimized for Streamlit applications.

```
┌─────────────────────────────────────────────────────────────┐
│                    Hugging Face Spaces                      │
│  ┌───────────────────────────────────────────────────────┐ │
│  │                  Streamlit Container                  │ │
│  │  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  │ │
│  │  │   app.py    │  │  src/       │  │ chroma_db/  │  │ │
│  │  │  (UI)       │─▶│  (RAG)      │─▶│ (vectors)   │  │ │
│  │  └─────────────┘  └─────────────┘  └─────────────┘  │ │
│  │                          │                            │ │
│  │                          ▼                            │ │
│  │                  ┌─────────────┐                      │ │
│  │                  │  Groq API   │                      │ │
│  │                  │ (External)  │                      │ │
│  │                  └─────────────┘                      │ │
│  └───────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────┘
                          │
                          ▼
                   ┌──────────────┐
                   │    Users     │
                   └──────────────┘
```

### Deployment Steps

1. **Prepare Repository**
   - Ensure `requirements.txt` includes all dependencies
   - Add Hugging Face Space metadata to README header (already present)
   - Verify `app_file: app.py` points to correct entry point

2. **Create Hugging Face Space**
   ```bash
   # Install Hugging Face CLI
   pip install huggingface_hub

   # Login to Hugging Face
   huggingface-cli login

   # Create new Space
   huggingface-cli repo create --type space --space_sdk streamlit system-design-assistant
   ```

3. **Deploy Application**
   ```bash
   # Add HF Space as git remote
   git remote add hf https://huggingface.co/spaces/md-asrar/system-design-assistant

   # Push to deploy
   git push hf main
   ```

4. **Configure Secrets**
   - Navigate to Space Settings → Repository Secrets
   - Add `GROQ_API_KEY` secret with your API key
   - Restart Space to apply changes

### Performance Optimization

**Cold Start Performance:**
- Initial model loading: ~8-10 seconds (within requirements)
- Embedding model cached with `@st.cache_resource`
- BM25 index cached with `@st.cache_resource`
- Vector store connection pooled

**Production Metrics (from evaluation):**
- Faithfulness: 0.324 (Ragas metric)
- Answer Relevancy: 0.454 (Ragas metric)
- Context Precision: 0.354 (Ragas metric)
- Retrieval p95: 176.8ms (PASS: <200ms target)
- End-to-end p95: 1625.8ms (PASS: <2000ms target)

### Known Limitations

**Corpus Coverage:**
- Currently indexes 10 GitHub repositories focused on system design
- Does not cover all possible system design topics
- May return "no relevant information" for niche or advanced topics

**Quality Metrics:**
- Faithfulness score of 0.324 indicates room for improvement in factual accuracy
- Prompt engineering and corpus expansion recommended for production use
- Citation discipline needs enhancement (some answers lack inline citations)

**Rate Limits:**
- Groq API free tier: 250 requests/day
- Shared across all Space users if using Space-level API key
- Recommend users provide their own API keys for heavy usage

**Scalability:**
- Single-instance deployment on Hugging Face Spaces
- No horizontal scaling or load balancing
- Suitable for portfolio/demo use, not production traffic

### Monitoring & Observability

**Metrics Dashboard:**
- Available in Streamlit sidebar (see app.py)
- Displays Ragas quality metrics and latency benchmarks
- Metrics loaded from evaluation results in `data/evaluation/`

**Logging:**
- Streamlit built-in logging captures errors
- Groq API errors logged to console
- No persistent log storage (Spaces restarts clear logs)

### Cost Analysis

**Free Tier Stack:**
- Hugging Face Spaces: Free (2 CPU cores, 16GB RAM)
- Groq API: Free (250 requests/day, 14,400 tokens/minute)
- ChromaDB: Self-hosted, no external costs
- Embedding models: Open-source, no API costs

**Total monthly cost: $0**

### Security Considerations

- API keys stored as Hugging Face Secrets (encrypted)
- No user authentication (public demo)
- No PII collection or storage
- HTTPS enforced by Hugging Face platform

---

## Roadmap

This project follows a 10-phase development plan focused on building a production-quality RAG application.

### Phase Overview

| Phase | Name | Status | Requirements |
|-------|------|--------|--------------|
| **1** | Project Foundation & Environment Setup | ✅ Complete | Infrastructure |
| **2** | Data Source Identification & Curation | 🔄 Next | INGS-01, INGS-02, INGS-03 |
| **3** | Document Processing & Chunking Pipeline | Pending | INGS-01, INGS-02, INGS-03 |
| **4** | Basic Retrieval Pipeline | Pending | RETR-01 |
| **5** | Hybrid Search & Retrieval Refinement | Pending | RETR-02 |
| **6** | LLM Integration & Answer Generation | Pending | GENR-01, GENR-02 |
| **7** | Chat Interface & Core UX | Pending | UIUX-01, UIUX-02, UIUX-03, UIUX-04 |
| **8** | UI Polish & Responsive Design | Pending | UIUX-05, UIUX-06 |
| **9** | Systematic Evaluation & Quality Assurance | Pending | Quality validation |
| **10** | Deployment & Documentation | Pending | Production readiness |

### Current Status

**Phase 1 Complete** (2026-02-07):
- ✅ Project structure with src/ layout
- ✅ Environment configuration system
- ✅ ChromaDB persistent client
- ✅ 163 production dependencies pinned
- ✅ Development tools configured
- ✅ Fresh clone validation

**Next Milestone**: Phase 2 - Curate 20-30 high-quality system design resources

---

## Contributing

This is a portfolio project built for learning and demonstration purposes. I'm not accepting external contributions at this time.

However, feel free to:
- **Fork** the repository for your own learning
- **Open issues** to report bugs or suggest improvements
- **Star** the project if you find it useful

---

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---

## Acknowledgments

- **System Design Resources**: [donnemartin/system-design-primer](https://github.com/donnemartin/system-design-primer)
- **RAG Best Practices**: Research from LlamaIndex, Pinecone, and Anthropic
- **Groq**: Free tier LLM inference for student projects

---

**Questions or feedback?** Open an issue on GitHub!

Built with ❤️ as a learning project in 2026.

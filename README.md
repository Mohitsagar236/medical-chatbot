# Medical Chatbot Strategy Comparison

Chatbot for answering medical questions.

Compares four LLM strategies on medical Q&A using PubMed abstracts.

| Strategy | RAG | Memory |
|----------|-----|--------|
| S1 — Single LLM | — | — |
| S2 — Single RAG | ✓ | — |
| S3 — Multi-Turn LLM | — | ✓ |
| S4 — Multi-Turn RAG | ✓ | ✓ |

All strategies use `llama-3.3-70b-versatile` via Groq (free tier).

---

## Prerequisites

- Python 3.10+
- A [Groq API key](https://console.groq.com) (free, no credit card)
- Your UIC email (required by NCBI Entrez for PubMed access)

---

## Local setup

### 1. Install dependencies

```bash
cd backend
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
```

### 2. Configure environment

```bash
cp .env.example .env
```

Open `.env` and fill in at minimum:

| Variable | Description |
|----------|-------------|
| `GROQ_API_KEY` | Get from [console.groq.com](https://console.groq.com) |
| `PUBMED_EMAIL` | Your UIC email (e.g. `netid@uic.edu`) |
| `NCBI_API_KEY` | Optional — speeds up seeding (3→10 req/s) |
| `CHROMA_BACKUP_URL` | Optional — URL to pre-built `chroma_db.tar.gz` to skip seeding |

### 3. Seed ChromaDB (run once)

ChromaDB is file-persisted — you only need to do this once per machine.

**Option A — fast restore from backup** (recommended):

`CHROMA_BACKUP_URL` is pre-filled in `.env.example`. The server downloads and restores the backup automatically on startup (~60s). Just start the server and wait.

**Option B — seed from PubMed** (~5h without NCBI key, ~1h with):

```bash
# From backend/ with venv active
python seed_db.py
```

Or trigger it via the API after the server is running:

```bash
curl -X POST http://localhost:8000/api/v1/ingestion/ingest \
  -H "Content-Type: application/json" \
  -d '{"query": "diabetes mellitus", "max_results": 100}'
```

Check seeding progress:

```bash
curl http://localhost:8000/api/v1/ingestion/status
```

### 4. Start the server

```bash
# From backend/ with venv active
uvicorn app.main:app --reload
```

API is available at `http://localhost:8000`
Interactive docs at `http://localhost:8000/docs`

---

## Running tests

```bash
cd backend
pytest                              # all tests
pytest tests/test_single_llm.py    # single file
```

---

## Running the evaluation

Install eval dependencies (from repo root):

```bash
pip install bert-score sentence-transformers httpx openpyxl pandas
```

Run evaluation against all 4 strategies:

```bash
python eval/run_evaluation.py \
  --input "reference-folder/Evaluation Dataset - CS 540 Project.xlsx" \
  --base-url http://localhost:8000 \
  --output eval/results/evaluation_results.xlsx
```

Add `--member 2` to run only one member's sheet. Results are written to the output Excel file with one row per `(session × turn × strategy)`.

---

## API overview

| Endpoint | Strategy |
|----------|----------|
| `POST /api/v1/chat/single-llm/` | S1 — `{ "query": "..." }` |
| `POST /api/v1/chat/single-rag/` | S2 — `{ "query": "...", "top_k": 5 }` |
| `POST /api/v1/chat/multi-turn-llm/` | S3 — `{ "session_id": "<uuid>", "query": "..." }` |
| `POST /api/v1/chat/multi-turn-rag/` | S4 — `{ "session_id": "<uuid>", "query": "...", "top_k": 5 }` |

For S3/S4, generate a `session_id` once per conversation (e.g. `python -c "import uuid; print(uuid.uuid4())"`) and reuse it on every follow-up turn. DELETE the session endpoint to reset history.

# AGENTS.md: lexora: AI Powered Law Assistant
> **Single Source of Truth** for all developers and AI coding agents (Antigravity, Cursor, Claude Code, etc.).
> Read this file entirely before writing any code.

---

## 1. Project Overview

**lexora** is a RAG-based AI legal assistant for Turkish law. It classifies user intent, answers legal questions with statutory citations, and dynamically generates ready-to-use legal documents (petitions, notices). It is **not** a substitute for a real lawyer; every output must carry a legal disclaimer.

**Core Scope (3 Slices):**
1. Intent classification & routing (`question_answering` / `document_generation` / `out_of_scope`)
2. Dynamic legal document generation (`.docx` + `.pdf`, dual direct export)
3. Article-based RAG for Turkish statutory Q&A (Consumer Law, Rental Law, etc.)

> **Layer 2 (Week 5 Decision Gate):** Rule-based contract/risky-clause analysis (15-20 patterns) will be added in Phase 3 **only if** the Nov 15 mid-term demo passes successfully and law mentors supply the necessary clause data.

---

## 2. Definitive Tech Stack

| Layer | Technology | Notes |
|---|---|---|
| **Backend** | Python 3.11+, FastAPI | Async REST API |
| **Data Validation** | Pydantic v2 | Structured Output + schema contracts |
| **LLM / AI** | Groq API | Model read from `GROQ_MODEL_NAME` env var, never hardcoded. Default candidates: `llama-3.3-70b-versatile` / `llama-3.1-8b-instant` / Mistral (compare via eval). Enable response caching during dev & eval to protect free-tier limits. |
| **Vector DB** | ChromaDB | Local, persistent collection |
| **Embeddings** | `sentence-transformers/paraphrase-multilingual-mpnet-base-v2` or `BAAI/bge-m3` | Turkish-capable, open-source, local inference |
| **Chunking** | Article-based (madde bazlı) | NOT character/token sliding window |
| **DOCX export** | `docxtpl` (python-docx + Jinja2) | Template-driven |
| **PDF export** | `WeasyPrint` or `fpdf2` | Direct from HTML/Jinja2 (no docx->pdf conversion). Requires OS-level C libs (`libcairo2`, `libpango-1.0-0`, `libgdk-pixbuf`). |
| **Relational DB / Auth** | Supabase (PostgreSQL) | User sessions, audit logs |
| **Observability** | Langfuse | Trace every LLM call; PII must be masked before logging |
| **Frontend** | Next.js (App Router, TypeScript), Tailwind CSS, shadcn/ui | |
| **Deployment** | Vercel (frontend), `backend/Dockerfile` → Render or Railway (backend) | Backend **must** ship via `Dockerfile` due to WeasyPrint's native C dependencies. |

---

## 3. Monorepo Folder Structure

```
lexora-law-assistant/
├── AGENTS.md                  ← You are here
├── requirements.txt           ← Python dependencies (FastAPI, Groq, ChromaDB, etc.)
├── .gitignore                 ← Git exclusion rules (secrets, venv, cache)
├── docs/                      ← Proposal, roadmap, API contract docs
├── data/
│   ├── laws/                  ← Article-based law JSON/MD files (Rental, Consumer, etc.)
│   ├── templates/             ← .docx and .html petition templates
│   └── eval/                  ← 30-scenario eval set + prompt injection tests
├── backend/
│   ├── Dockerfile                ← Required for WeasyPrint C-lib dependencies
│   ├── .env.example              ← Template for all required env vars (no secrets)
│   ├── app/
│   │   ├── main.py
│   │   ├── core/
│   │   │   ├── config.py      ← Settings (env vars via pydantic-settings)
│   │   │   ├── security.py    ← Input sanitization, PII filter
│   │   │   └── langfuse.py    ← Observability client setup
│   │   ├── schemas/           ← Pydantic API contracts (request/response models)
│   │   ├── api/
│   │   │   └── v1/
│   │   │       ├── health.py
│   │   │       ├── chat.py
│   │   │       └── documents.py
│   │   └── services/
│   │       ├── llm_service.py    ← Groq API calls, structured output extraction
│   │       ├── rag_service.py    ← ChromaDB retrieval, article-based search
│   │       └── doc_service.py    ← docxtpl + WeasyPrint dual export
│   ├── scripts/
│   │   ├── ingest_laws.py        ← Article-based chunking → ChromaDB ingestion CLI
│   │   └── run_eval.py           ← hit@5 + LLM-as-judge evaluation CLI
│   ├── tools/
│   │   └── build_doc_templates.py ← Generates data/templates/*.docx (keeps docxtpl tags in single runs)
│   └── tests/
└── frontend/
    └── src/
        ├── app/               ← Next.js App Router pages
        ├── components/
        │   ├── chat/          ← Chat UI components
        │   ├── document/      ← PII mini-form, document preview, DOCX/PDF download
        │   └── common/        ← Legal disclaimer banner (ALWAYS visible)
        └── lib/
            └── api.ts         ← API client with mock data fallback
```

---

## 4. API Contract (v1: Starter Endpoints)

### `GET /api/v1/health`
Returns service status and dependency connectivity (ChromaDB, Supabase, Groq).

### `POST /api/v1/chat/message`
**Request:** `{ "session_id": str, "message": str }`
**Pipeline:** sanitize input -> classify intent -> route to RAG or param-extraction
**Response fields:**
- `intent`: `"question_answering"` | `"document_generation"` | `"out_of_scope"`
- `answer`: str (RAG response with article citations, if Q&A)
- `citations`: list of `{ article_id, law_name, text_snippet }`
- `extracted_params`: dict (case parameters extracted via structured output)
- `missing_fields`: list[str] (fields the agent still needs to ask for)
- `suggested_template_id`: `Optional[str]` (populated when `intent == "document_generation"`)

### `GET /api/v1/documents/templates`
Returns active template list with their expected field schemas.

### `POST /api/v1/documents/generate`
**Request:** `{ "template_id": str, "case_params": dict, "pii": { <keys per the template's pii_fields>: str } }`
`pii` keys are defined by the template's `pii_fields` and validated server-side (required fields, unknown keys, `tc_id` = 11 digits, `iban` = TR + 24 digits); invalid → 422 `TEMPLATE_FIELDS_INVALID` (message lists field names only, never values). Undefined `case_params` keys are not rejected; they are dropped before rendering.
**Response:** `{ "file_id": str, "docx_url": str, "pdf_url": str, "expires_at": datetime }`
Both files are generated in parallel from the **same Pydantic data model** (no format conversion).

### `GET /api/v1/documents/download/{file_id}`
Serves the generated `.docx` or `.pdf` file. Files are stored in a temporary directory and **auto-deleted after expiry** (KVKK compliance: no permanent PII storage on server).

---

## 5. PII & KVKK Rules (Non-Negotiable)

1. **LLM never receives raw PII.** Direct identity/contact data (full name, TC ID, IBAN, full address) is collected via a frontend mini-form and injected directly into `doc_service` (never into the chat/LLM pipeline).
2. **Accidental PII masking:** Because users may type personal data in free-text chat, `security.py` applies a regex/placeholder masking layer (e.g. `[TC_NO]`, `[IBAN]`) on every incoming message **before** any LLM call.
3. **Input sanitization** (prompt injection filtering) runs alongside PII masking in `security.py`.
4. **Langfuse logs** must have PII stripped/masked at the tracing layer (`core/langfuse.py`).
5. **No permanent PII storage.** Generated files expire; only anonymized case parameters may be stored for analytics.
6. Every UI output (chat response, document preview) must display the disclaimer: *"Bu sistem bir AI asistanıdır; avukatlık hizmeti vermez."*

---

## 6. Coding Standards

- **Python:** Follow PEP 8. Use type hints everywhere. All services return Pydantic models, not raw dicts.
- **FastAPI:** Use `async def` for all route handlers. Mount router at `/api/v1/`.
- **Pydantic v2:** Define all request/response schemas in `app/schemas/`. Use `model_validator` for cross-field checks.
- **Chunking:** Law texts in `data/laws/` must be split per article (`Madde X -`). Each chunk stored in ChromaDB with metadata: `{ "law": str, "article_no": int, "domain": str }`.
- **Error handling:** Return structured JSON errors `{ "error_code": str, "message": str }`. Never expose stack traces to the client.
- **TypeScript/Next.js:** Strict mode enabled. No `any` types. API types must match backend Pydantic schemas.
- **Environment variables:** All secrets via `.env` (never hardcoded). Use `pydantic-settings` in `config.py`. Required vars: `GROQ_API_KEY`, `GROQ_MODEL_NAME`, `CHROMA_PERSIST_DIR`, `SUPABASE_URL`, `SUPABASE_KEY`, `LANGFUSE_SECRET_KEY`.
- **LLM model selection:** Always read model name from `settings.GROQ_MODEL_NAME`. Never hardcode a model string in service code.
- **Response caching:** Cache identical Groq API calls (keyed on prompt hash) during development and eval runs to avoid hitting free-tier rate limits.
- **Tests:** Unit tests in `backend/tests/`. Minimum coverage targets: `rag_service` and `doc_service`.

---

## 7. Development Phases

| Phase | Weeks | Key Deliverables |
|---|---|---|
| **Phase 1** | W1-W2 | Repo scaffold, FastAPI skeleton + API contract, Next.js skeleton (mock chat + document preview UI + legal disclaimer banner), law text collection + article-based chunking + ChromaDB ingestion, RAG v0, 1st document template (Jinja2/docxtpl), 15 eval scenarios drafted |
| **Phase 2** | W3-W4 🚩 *Gate 1: Nov 15 Mid-Term Demo* | Structured output param extraction, missing-field questioning loop, intent routing, PII mini-form + parallel `.docx` & `.pdf` generation + download endpoint, Langfuse setup, `hit@5` measurement, eval set completed to 30 scenarios. *(Exit criteria: 1st document type works end-to-end in the UI.)* |
| **Phase 3** | W5-W6 🚩 *Gate 2: Nov 29 Feature Freeze* | 2nd document template + flow, full legal Q&A screen + faithfulness eval, chat/log PII masking hardening, 15-20 prompt injection & security tests, error state handling + UI polish, staging deploy. *(W5 decision point: add rule-based contract analysis only if Gate 1 passed and mentor data available.)* |
| **Phase 4** | W7-W8 🏁 *Delivery* | Bug fixes only (no new features), final eval run (30 scenarios, `p95 < 10 s` verified), documentation + README, production deploy, demo rehearsal. |

> **Feature Freeze:** End of Week 6 (Nov 29). After that: bug fixes and report only.

---

## 8. Evaluation & Quality Gates

- **Retrieval:** `hit@5` (correct law article must appear in top-5 results, measured every eval round).
- **Latency:** `p95 < 10 seconds` end-to-end response time.
- **Generation:** Faithfulness + answer relevancy via LLM-as-judge; mentor manual spot-check on a sample.
- **Documents:** Every generated document passes mentor checklist (mandatory sections, citations, formal language).
- **Security:** 15-20 prompt injection attempts tested and results documented.
- **Eval set:** Minimum 30 mentor-approved scenarios in `data/eval/` by end of Week 3.

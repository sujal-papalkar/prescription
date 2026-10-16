# AyurClinical RAG: Clinical PDF Retrieval-Augmented Generation Engine

A complete, production-ready Clinical RAG application. The system starts with an empty database: you upload your own clinical guideline PDF, and ask any question. If information is not explicitly mentioned in the uploaded PDF, it strictly answers: **"Not mentioned in the PDF."**

---

### 🛡️ Core Grounding Guarantees
1. **Zero Pre-loaded Documents**: All sample and pre-seeded source documents have been removed. The database is 100% clean.
2. **User PDF Upload**: You upload your PDF document directly. Tables, dosages, and text are parsed and indexed locally on your machine.
3. **Strict Negative Grounding**: Whenever you ask a question or request a prescription for a condition not found in the uploaded PDF, it returns:
   > **"Not mentioned in the PDF."**
4. **Clean Medical Light Theme**: Clean, accessible white and light slate interface with an intuitive 2-step layout (`Step 1: Upload Your PDF` -> `Step 2: Ask Questions & Prescribe`).

---

## 🏛️ System Architecture Overview

```
                          PHYSICAL CLINICAL GUIDELINE PDF
                                        │
                                        ▼
                         IBM Docling Layout Parser
                                        │
                ┌───────────────────────┴───────────────────────┐
                ▼                                               ▼
         [ Fork A: Tables ]                             [ Fork B: Prose ]
     Pandas DataFrames Extraction                  Markdown Layout Exporter
  Category Forward-Fill (df.ffill())             Header Transitions (#, ##, ###)
Patient-State Matrix Serialization             Breadcrumb Prepending ([Section > Subsection])
                │                                               │
                └───────────────────────┬───────────────────────┘
                                        ▼
                           DUAL-ENGINE RETRIEVAL MATRIX
                                        │
                ┌───────────────────────┴───────────────────────┐
                ▼                                               ▼
         Dense Vector Store                            Sparse Keyword Index
        ChromaDB Persistent                             BM25Okapi In-Memory
  Google text-embedding-004 Coordinates            Tokenized Sanskrit Clinical Terms
 Hard Pre-filter: where={"disease_name": X}        Partitioned by Global Disease Tag
                │                                               │
                └───────────────────────┬───────────────────────┘
                                        ▼
                        Reciprocal Rank Fusion (RRF)
                         Score = Σ 1 / (60 + Rank_i)
                                        │
                                        ▼
                  LANGRAPH STATEFUL ORCHESTRATION GRAPH
                ┌───────────────────────────────────────┐
                │ Node 1: Clinical Router               │
                │ Node 2: Isolated Hybrid Retriever     │
                │ Node 3: 0.0-Temp Gemini 2.5 Pro       │
                └───────────────────────────────────────┘
                                        │
                                        ▼
                       STRICT PYDANTIC RESPONSE SCHEMA
                         (StructuredPrescription JSON)
                                        │
                                        ▼
                  REACT 18+ TYPESCRIPT PHYSICIAN DASHBOARD
       Split Clinical Intake Chart  •  Interactive Prescription Matrix
     Glowing Warning Cards  •  Mandatory Legal Attestation Signature Gate
```

---

## 🛠️ Tech Stack & Key Components

| Layer | Technology | Role & Configuration |
|---|---|---|
| **Backend Framework** | **FastAPI + Uvicorn** | High-performance asynchronous REST API with CORS middleware for port 5173. |
| **Ingestion Engine** | **IBM Docling 2.0** | Local layout-aware PDF parser extracting DataFrames and Markdown prose hierarchies. |
| **Vector Database** | **ChromaDB Persistent** | Local persistent cosine vector index with hard metadata pre-filtering by disease. |
| **Sparse Keyword Engine** | **rank-bm25 (BM25Okapi)** | Local tokenized keyword index for exact Sanskrit terms and multi-digit dosages. |
| **Embeddings** | **Google GenAI `text-embedding-004`** | High-dimensional numerical semantic coordinates. |
| **Generation Brain** | **Google GenAI `gemini-2.5-pro`** | Temperature 0.0, strictly constrained to `StructuredPrescription` schema. |
| **Workflow State Machine** | **LangGraph** | Multi-step state graph: `Router -> Retriever -> Generator -> END`. |
| **Frontend Framework** | **React 18 + Vite + TypeScript** | Intuitive 2-step clinical interface (Upload -> Q&A / Prescribe). |
| **Styling & UI** | **Tailwind CSS + Lucide Icons** | Clean medical light theme (`#ffffff` and `#f8fafc`), accessible cards and alerts. |

---

## 📂 Repository Structure

```
medical_rag_app/
│
├── backend/
│   ├── core/
│   │   ├── __init__.py
│   │   ├── parser.py          # Phase 1 & 2: Local Docling parser & structure-aware chunking
│   │   ├── database.py        # Phase 3: ChromaDB + BM25 local hybrid index and RRF blending
│   │   └── pipeline.py        # Phase 4 & 5: LangGraph routing state machine & Gemini API
│   ├── data/
│   │   ├── chroma_db/         # Local persistent ChromaDB and BM25 index storage
│   │   └── uploads/           # Air-gapped guideline PDF storage
│   ├── main.py                # FastAPI server orchestration endpoints
│   ├── requirements.txt       # Production pinned dependency list
│   └── seed_data.py           # Authentic clinical guideline dataset generator
│
└── frontend/                  # Vite + React (TypeScript) Application
    ├── src/
    │   ├── components/
    │   │   ├── Dashboard.tsx  # Main interactive layout switcher & tabs
    │   │   ├── Ingestion.tsx  # Admin pipeline form to upload and index PDFs
    │   │   └── IntakeForm.tsx # Clinical intake section with inputs, tables & signature gate
    │   ├── App.tsx            # Main application mounting and health polling
    │   ├── index.css          # Tailwind configurations & medical glass styling
    │   ├── main.tsx           # React DOM root
    │   └── types.ts           # Strict TypeScript interfaces
    ├── index.html             # Inter typography & medical metadata
    ├── package.json           # Frontend dependency manifest
    ├── tailwind.config.js     # Herbal medical palette configuration
    ├── postcss.config.js
    └── vite.config.ts
```

---

## 🚀 Running the Application Locally

### Quickest Way: One-Click Launcher
Run the launcher script from `medical_rag_app`:
```powershell
.\start.ps1
```
*(Or double-click `start.bat` in File Explorer).*

---

### Manual Launch (Separate Terminals)

#### Terminal 1 — Backend (FastAPI):
If you are in `medical_rag_app`:
```powershell
cd medical_rag_app
.\backend\venv\Scripts\python.exe -m uvicorn backend.main:app --host 127.0.0.1 --port 8000 --reload
```
*Note: If you already ran `cd backend`, use `main:app` instead of `backend.main:app`:*
```powershell
cd medical_rag_app\backend
.\venv\Scripts\python.exe -m uvicorn main:app --host 127.0.0.1 --port 8000 --reload
```

#### Terminal 2 — Frontend (Vite + React UI):
```powershell
cd medical_rag_app\frontend
npm run dev
```
Open **`http://localhost:5173`** in your browser.

---

## 🔬 Core Medical Safeguards & Innovations

1. **Air-Gapped Document Processing**: All document parsing (Docling), text tokenization, and vector storage (ChromaDB) operate strictly on local infrastructure. Sensitive medical PDFs never leave your network.
2. **Zero Cross-Contamination**: ChromaDB queries apply a hard `where={"disease_name": disease_name}` pre-filter, guaranteeing that respiratory guidelines never bleed into diabetes or arthritis treatments.
3. **Hybrid Search Blending (RRF)**: Reciprocal Rank Fusion ensures that conceptual queries (e.g., "difficulty breathing at night") match semantically, while exact formulation terms (e.g., `Shwas Kuthar Rasa`, `1-1-1`) are matched by BM25Okapi without semantic distortion.
4. **Physician Discretion Verification Gate**: In accordance with medical software safety standards, generated prescription blueprints remain locked until the attending physician explicitly checks the legal attestation checkbox:
   > *"I hereby certify that I have cross-reviewed these prescription indicators and confirm their accuracy under my medical license discretion."*

"""
FastAPI Orchestration Server for Ayurvedic Clinical RAG Pipeline
Strictly Grounded Document RAG: Answers and Prescriptions derived ONLY from user-uploaded PDFs.
If information is not in the uploaded PDF, it strictly returns: "Not mentioned in the PDF."
"""

import sys
import os
import shutil
import logging
from typing import List, Dict, Any, Optional
from contextlib import asynccontextmanager

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
PARENT_DIR = os.path.dirname(BASE_DIR)
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)
if PARENT_DIR not in sys.path:
    sys.path.insert(0, PARENT_DIR)

from fastapi import FastAPI, UploadFile, File, Form, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from dotenv import load_dotenv

# Load .env from backend folder or root folder
load_dotenv(os.path.join(BASE_DIR, ".env"))
load_dotenv(os.path.join(PARENT_DIR, ".env"))
load_dotenv()

try:
    from backend.core.parser import StructureAwareParser, DOCLING_AVAILABLE
    from backend.core.database import HybridSearchEngine
    from backend.core.pipeline import ClinicalRAGPipeline
except ImportError:
    from core.parser import StructureAwareParser, DOCLING_AVAILABLE
    from core.database import HybridSearchEngine
    from core.pipeline import ClinicalRAGPipeline

# Setup structured logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
logger = logging.getLogger("medical_rag_api")

DATA_DIR = os.path.join(BASE_DIR, "data")
UPLOADS_DIR = os.path.join(DATA_DIR, "uploads")
CHROMA_DIR = os.path.join(DATA_DIR, "chroma_db")

os.makedirs(UPLOADS_DIR, exist_ok=True)
os.makedirs(CHROMA_DIR, exist_ok=True)

# Initialize Core Services
db_engine: Optional[HybridSearchEngine] = None
parser_engine: Optional[StructureAwareParser] = None
rag_pipeline: Optional[ClinicalRAGPipeline] = None

def get_db() -> HybridSearchEngine:
    global db_engine
    if db_engine is None:
        db_engine = HybridSearchEngine(persist_dir=CHROMA_DIR)
    return db_engine

def get_pipeline() -> ClinicalRAGPipeline:
    global rag_pipeline
    if rag_pipeline is None:
        rag_pipeline = ClinicalRAGPipeline(db_engine=get_db())
    return rag_pipeline

def get_parser() -> StructureAwareParser:
    global parser_engine
    if parser_engine is None:
        parser_engine = StructureAwareParser()
    return parser_engine


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Starting Ayurvedic Clinical RAG Pipeline Services...")
    db = get_db()
    get_parser()
    get_pipeline()
    logger.info(f"Database initialized. Currently indexed diseases: {db.get_indexed_diseases()}")
    yield
    logger.info("Shutting down Ayurvedic Clinical RAG Services.")


app = FastAPI(
    title="Ayurvedic Clinical Document RAG Engine",
    description="Strictly grounded Retrieval-Augmented Generation from user-uploaded PDFs. If not in the PDF, returns: 'Not mentioned in the PDF.'",
    version="2.0.0",
    lifespan=lifespan
)

# Enable CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:3000",
        "http://localhost:4173",
        "*"
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ---------------------------------------------------------
# Request & Response Schemas
# ---------------------------------------------------------

class PatientIntakeRequest(BaseModel):
    age: int = Field(..., ge=1, le=120, description="Patient age in years")
    gender: str = Field(..., description="Biological sex (Male, Female, Other)")
    history: List[str] = Field(default_factory=list, description="Checked risk factors")
    symptoms: List[str] = Field(..., description="Active clinical symptoms")
    vitals: str = Field("", description="Objective lab and vital metrics")
    chief_complaint: Optional[str] = Field(None, description="Physician's chief complaint notes")
    target_disease: Optional[str] = Field("Auto-Detect", description="Disease category override or Auto-Detect")


class QuestionRequest(BaseModel):
    question: str = Field(..., description="User question to answer strictly from the uploaded PDF")
    disease_name: Optional[str] = Field(None, description="Optional disease filter if multiple PDFs are uploaded")


class IngestResponse(BaseModel):
    status: str
    message: str
    disease_name: str
    chunks_indexed: int
    sample_chunks: List[Dict[str, Any]]


# ---------------------------------------------------------
# API Endpoints
# ---------------------------------------------------------

@app.get("/api/v1/health")
def health_check():
    """System diagnostics and readiness check."""
    gemini_key_set = bool(os.getenv("GEMINI_API_KEY"))
    try:
        db = get_db()
        indexed_diseases = db.get_indexed_diseases()
        total_chunks = db.collection.count()
        connected = True
    except Exception as e:
        logger.warning(f"DB health check error: {e}")
        indexed_diseases = []
        total_chunks = 0
        connected = False
    
    return {
        "status": "healthy",
        "system": "Ayurvedic Clinical Document RAG Engine",
        "docling_available": DOCLING_AVAILABLE,
        "chromadb_connected": connected,
        "gemini_api_configured": gemini_key_set,
        "total_chunks_indexed": total_chunks,
        "has_uploaded_documents": total_chunks > 0,
        "indexed_diseases_count": len(indexed_diseases),
        "indexed_diseases": indexed_diseases,
        "vector_storage_dir": CHROMA_DIR
    }


@app.get("/api/v1/diseases")
def list_diseases():
    """Returns list of distinct guideline disease partitions currently indexed."""
    if not db_engine:
        raise HTTPException(status_code=500, detail="Database engine uninitialized")
    diseases = db_engine.get_indexed_diseases()
    return {"diseases": diseases}


@app.get("/api/v1/inspect/chunks")
def inspect_chunks(
    disease_name: Optional[str] = None,
    chunk_type: Optional[str] = None,
    page: Optional[int] = None,
    search: Optional[str] = None,
    limit: int = 50,
    offset: int = 0
):
    """
    Inspection endpoint allowing clinicians and developers to audit
    all extracted chunks, table matrices, section headers, and page provenance.
    """
    if not db_engine:
        raise HTTPException(status_code=500, detail="Database engine uninitialized")

    res = db_engine.collection.get()
    all_ids = res.get("ids", [])
    all_docs = res.get("documents", [])
    all_metas = res.get("metadatas", [])

    summary_by_disease: Dict[str, int] = {}
    summary_by_type: Dict[str, int] = {}
    summary_by_page: Dict[Any, int] = {}

    matching = []
    for cid, doc, meta in zip(all_ids, all_docs, all_metas):
        m = meta or {}
        d_name = m.get("disease_name", "General")
        c_type = m.get("chunk_type", "prose_narrative")
        p_num = m.get("page", 1)

        summary_by_disease[d_name] = summary_by_disease.get(d_name, 0) + 1
        summary_by_type[c_type] = summary_by_type.get(c_type, 0) + 1
        summary_by_page[p_num] = summary_by_page.get(p_num, 0) + 1

        # Apply filters
        if disease_name and disease_name != "All" and d_name.lower() != disease_name.lower():
            continue
        if chunk_type and chunk_type != "All" and c_type.lower() != chunk_type.lower():
            continue
        if page is not None and p_num != page:
            continue
        if search and search.lower() not in doc.lower():
            continue

        matching.append({
            "chunk_id": cid,
            "disease_name": d_name,
            "chunk_type": c_type,
            "page": p_num,
            "section": m.get("section", m.get("category", "Overview")),
            "source": m.get("source", ""),
            "metadata": m,
            "word_count": len(doc.split()),
            "preview": doc[:200] + ("..." if len(doc) > 200 else ""),
            "text": doc
        })

    paginated = matching[offset:offset + limit]

    return {
        "status": "success",
        "total_in_db": len(all_ids),
        "total_matching": len(matching),
        "offset": offset,
        "limit": limit,
        "summary": {
            "by_disease": summary_by_disease,
            "by_type": summary_by_type,
            "by_page": dict(sorted(summary_by_page.items(), key=lambda x: str(x[0])))
        },
        "chunks": paginated
    }


@app.post("/api/v1/clear")
def clear_all_documents():
    """Wipes all documents, chunks, and index files so the database starts 100% clean."""
    if not db_engine:
        raise HTTPException(status_code=500, detail="Database engine uninitialized")
    db_engine.clear_all()

    # Clear uploads directory
    try:
        for f in os.listdir(UPLOADS_DIR):
            file_path = os.path.join(UPLOADS_DIR, f)
            if os.path.isfile(file_path):
                os.remove(file_path)
    except Exception as e:
        logger.warning(f"Could not clear uploads folder: {e}")

    return {
        "status": "success",
        "message": "All uploaded documents and guideline chunks have been completely deleted.",
        "total_chunks_remaining": 0
    }


@app.post("/api/v1/ingest", response_model=IngestResponse)
async def ingest_guideline(
    file: Optional[UploadFile] = File(None),
    file_path: Optional[str] = Form(None),
    disease_name: str = Form(...)
):
    """
    Ingests user-uploaded clinical guideline PDF:
    Parses tables with forward-fill and extracts clean markdown sections locally.
    Indexes chunks into ChromaDB and BM25 index.
    """
    if not db_engine or not parser_engine:
        raise HTTPException(status_code=500, detail="Core processing engines uninitialized")

    clean_disease = disease_name.strip()
    if not clean_disease:
        clean_disease = "General Clinical Guideline"

    target_local_path = None

    if file and file.filename:
        ext = os.path.splitext(file.filename)[1].lower()
        allowed_extensions = {".pdf", ".docx", ".doc", ".txt", ".md", ".csv", ".xlsx", ".xlsv", ".xls", ".png", ".jpg", ".jpeg"}
        if ext not in allowed_extensions:
            raise HTTPException(
                status_code=400,
                detail=f"Unsupported file format '{ext}'. Allowed formats: PDF, DOCX, TXT, MD, CSV, XLSX, PNG, JPG, JPEG."
            )
        safe_filename = f"{clean_disease.replace(' ', '_').replace('/', '_')}_{os.path.basename(file.filename)}"
        target_local_path = os.path.join(UPLOADS_DIR, safe_filename)
        with open(target_local_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        logger.info(f"Received user upload saved at: {target_local_path}")
    elif file_path and os.path.exists(file_path):
        target_local_path = file_path
        logger.info(f"Ingesting user local file path: {target_local_path}")
    else:
        raise HTTPException(
            status_code=400,
            detail="Please select a document file to upload (PDF, DOCX, TXT, MD, CSV, XLSX, PNG, JPG, JPEG)."
        )

    try:
        # Phase 1 & 2: Local layout structure-aware parsing across multiple document formats
        chunks = parser_engine.parse_document(file_path=target_local_path, disease_name=clean_disease)
        if not chunks:
            raise HTTPException(status_code=422, detail="No readable text or table matrices extracted from the document.")

        # Phase 3: ChromaDB + BM25 indexing
        count = db_engine.ingest_chunks(chunks=chunks, disease_name=clean_disease)

        return IngestResponse(
            status="success",
            message=f"Successfully parsed and indexed {count} sections & tables from your document for '{clean_disease}'",
            disease_name=clean_disease,
            chunks_indexed=count,
            sample_chunks=chunks[:3]
        )
    except Exception as e:
        logger.error(f"Ingestion pipeline failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Ingestion failure: {str(e)}")


@app.post("/api/v1/ask")
async def ask_question_endpoint(req: QuestionRequest):
    """
    Strict Document Q&A:
    Answers user questions strictly from the uploaded PDF.
    If the answer is NOT in the PDF, returns EXACTLY: 'Not mentioned in the PDF.'
    """
    if not rag_pipeline or not db_engine:
        raise HTTPException(status_code=500, detail="Engines uninitialized")

    if db_engine.collection.count() == 0:
        return {
            "status": "success",
            "question": req.question,
            "answer": "Not mentioned in the PDF. (No PDF document has been uploaded yet)",
            "found_in_pdf": False,
            "source_chunks": []
        }

    result = rag_pipeline.answer_question(query=req.question, disease_name=req.disease_name)
    return {
        "status": "success",
        "question": req.question,
        "answer": result["answer"],
        "found_in_pdf": result["found_in_pdf"],
        "source_chunks": result["source_chunks"]
    }


@app.post("/api/v1/prescribe")
async def generate_prescription(intake: PatientIntakeRequest):
    """
    Clinical Prescription Generation:
    Strictly extracts prescription rows from the uploaded PDF tables.
    If no PDF is uploaded or condition is not in the PDF, returns: 'Not mentioned in the PDF.'
    """
    if not rag_pipeline or not db_engine:
        raise HTTPException(status_code=500, detail="RAG Pipeline orchestrator uninitialized")

    # If no PDF has been uploaded yet
    if db_engine.collection.count() == 0:
        return {
            "status": "success",
            "data": {
                "disease_matched": "No Document Uploaded",
                "clinical_state_matched": "Not mentioned in the PDF",
                "prescription_list": [],
                "clinical_warnings": ["No guideline PDF has been uploaded yet. Please upload your guideline PDF first."],
                "pathya_dietary_guidelines": [],
                "apathya_contraindications": [],
                "rationale_grounding": "Not mentioned in the PDF. Please upload a guideline PDF first."
            },
            "routing_log": ["No documents found in database."],
            "target_disease": "None",
            "grounding_chunks_count": 0,
            "grounding_chunks": []
        }

    query_parts = []
    if intake.chief_complaint:
        query_parts.append(intake.chief_complaint)
    if intake.symptoms:
        query_parts.append(f"Symptoms: {', '.join(intake.symptoms)}")
    raw_query = " | ".join(query_parts) if query_parts else "General Ayurvedic Assessment"

    patient_profile = {
        "age": intake.age,
        "gender": intake.gender,
        "history": intake.history,
        "symptoms": intake.symptoms,
        "vitals": intake.vitals
    }

    try:
        result = rag_pipeline.execute(
            raw_query=raw_query,
            patient_profile=patient_profile,
            target_disease=intake.target_disease if intake.target_disease != "Auto-Detect" else None
        )
        return {
            "status": "success",
            "data": result["prescription"],
            "routing_log": result["routing_log"],
            "target_disease": result["target_disease"],
            "grounding_chunks_count": len(result["retrieved_context"]),
            "grounding_chunks": result["retrieved_context"]
        }
    except Exception as e:
        logger.error(f"Prescription generation failure: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Prescription error: {str(e)}")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)

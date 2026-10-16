export interface PrescriptionItem {
  medicine_name: string;
  matra: string;
  sahpaan: string;
  aushadh_kal: string;
}

export interface StructuredPrescription {
  disease_matched: string;
  clinical_state_matched: string;
  prescription_list: PrescriptionItem[];
  clinical_warnings: string[];
  pathya_dietary_guidelines?: string[];
  apathya_contraindications?: string[];
  rationale_grounding: string;
}

export interface GroundingChunk {
  chunk_id: string;
  text: string;
  metadata: {
    disease_name: string;
    source: string;
    chunk_type: string;
    table_index?: number;
    row_index?: number;
    section?: string;
  };
  rrf_score: number;
  matched_engines: string[];
}

export interface PrescriptionResponse {
  status: string;
  data: StructuredPrescription;
  routing_log: string[];
  target_disease: string;
  grounding_chunks_count: number;
  grounding_chunks: GroundingChunk[];
}

export interface QuestionResponse {
  status: string;
  question: string;
  answer: string;
  found_in_pdf: boolean;
  source_chunks: Array<{
    chunk_id?: string;
    text: string;
    metadata?: Record<string, any>;
  }>;
}

export interface SystemHealth {
  status: string;
  system: string;
  docling_available: boolean;
  chromadb_connected: boolean;
  gemini_api_configured: boolean;
  total_chunks_indexed?: number;
  has_uploaded_documents?: boolean;
  indexed_diseases_count: number;
  indexed_diseases: string[];
  vector_storage_dir: string;
}

export interface IngestResponse {
  status: string;
  message: string;
  disease_name: string;
  chunks_indexed: number;
  sample_chunks: Array<{
    text: string;
    metadata: Record<string, any>;
  }>;
}

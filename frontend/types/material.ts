// Mirrors backend/app/schemas/*.py exactly. Keep these in sync if the
// backend schemas change -- they are the contract between frontend/backend.

export interface DocumentOut {
  id: number;
  project_id: number;
  filename: string;
  content_type: string | null;
  page_count: number;
  ocr_status: "pending" | "processing" | "completed" | "failed";
  uploaded_at: string;
}

export interface ProjectOut {
  id: number;
  name: string;
  status: string;
  created_at: string;
  documents: DocumentOut[];
}

export interface ProjectSummary {
  id: number;
  name: string;
  status: string;
  created_at: string;
}

export interface UploadResponse {
  project: ProjectOut;
  message: string;
}

export interface Material {
  id: number;
  material_name: string;
  category: string;
  procurement_stage: string;
  secondary_stage: string | null;
  quantity: number | null;
  unit: string | null;
  confidence: number;
  evidence: string;
  source_document: string;
  source_page: number | null;
  extraction_method: string;
}

export interface ReasoningTrace {
  id: number;
  material_id: number;
  what_detected: string;
  where_detected: string;
  why_category: string;
  why_stage: string;
  confidence_explanation: string;
  full_text: string;
}

export interface MaterialWithReasoning extends Material {
  reasoning: ReasoningTrace | null;
}

export interface ProcurementStageGroup {
  stage: string;
  order: number;
  item_count: number;
  materials: Material[];
}

export interface ProcurementPlan {
  project_id: number;
  stages: ProcurementStageGroup[];
}

export interface AnalyzeDocumentResult {
  document: string;
  status: "completed" | "failed";
  pages?: number;
  materials_found?: number;
  reason?: string;
}

export interface AnalyzeResponse {
  project_id: number;
  status: string;
  documents: AnalyzeDocumentResult[];
}

export interface SearchResultItem {
  content_type: "ocr_page" | "material" | "reasoning";
  content_id: number;
  project_id: number | null;
  snippet: string;
  document_name: string | null;
  page_number: number | null;
  score: number | null;
}

export interface SearchResponse {
  query: string;
  results: SearchResultItem[];
}

export interface AskResponse {
  question: string;
  answer: string;
  grounded: boolean;
  citations: SearchResultItem[];
  note?: string | null;
}

export interface HealthResponse {
  status: string;
  service: string;
  azure_ocr_configured: boolean;
  llm_configured: boolean;
}
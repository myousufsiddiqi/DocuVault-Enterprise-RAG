export type SearchMode = 'hybrid' | 'vector' | 'keyword';

export interface LineItem {
  description: string;
  quantity: number;
  unit_price: number;
  total: number;
}

export interface InvoiceExtraction {
  invoice_number: string;
  invoice_date: string;
  due_date?: string;
  vendor_name: string;
  vendor_address?: string;
  customer_name: string;
  customer_address?: string;
  line_items: LineItem[];
  subtotal: number;
  tax_amount: number;
  discount_amount: number;
  grand_total: number;
  currency: string;
}

export interface IngestTelemetry {
  parse_time_ms: number;
  chunk_time_ms: number;
  embedding_time_ms: number;
  extraction_time_ms: number;
  extraction_retries: number;
  total_time_ms: number;
  estimated_prompt_tokens: number;
  estimated_completion_tokens: number;
  cost_usd: number;
}

export interface IngestResponse {
  document_id: string;
  filename: string;
  file_size_bytes: number;
  page_count: number;
  total_chunks: number;
  extraction: InvoiceExtraction;
  extraction_validation_passed: boolean;
  telemetry: IngestTelemetry;
}

export interface ChunkSearchResult {
  chunk_id: string;
  document_id: string;
  filename: string;
  page_number: number;
  chunk_index: number;
  content: string;
  vector_score?: number;
  keyword_score?: number;
  rrf_score?: number;
  rerank_score?: number;
  final_rank: number;
}

export interface SearchTelemetry {
  dense_time_ms: number;
  sparse_time_ms: number;
  rrf_time_ms: number;
  rerank_time_ms: number;
  total_time_ms: number;
}

export interface SearchResponse {
  query: string;
  mode: SearchMode;
  rerank_applied: boolean;
  total_candidates_retrieved: number;
  results: ChunkSearchResult[];
  telemetry: SearchTelemetry;
}

export interface SystemHealth {
  status: string;
  environment: string;
  database: {
    status: string;
    pgvector_extension: string;
    pgvector_version?: string;
  };
  providers: {
    mode: string;
    extraction_provider: string;
    extraction_model: string;
    embedding_provider: string;
    embedding_model: string;
    embedding_dimensions: number;
    rerank_provider: string;
    rerank_model: string;
  };
}

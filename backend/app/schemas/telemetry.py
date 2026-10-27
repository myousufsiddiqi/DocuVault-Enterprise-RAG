from typing import Optional
from uuid import UUID
from pydantic import BaseModel, Field

from app.schemas.extraction import InvoiceExtractionSchema


class IngestTelemetry(BaseModel):
    """Execution telemetry for document ingestion."""
    parse_time_ms: float = 0.0
    chunk_time_ms: float = 0.0
    embedding_time_ms: float = 0.0
    extraction_time_ms: float = 0.0
    extraction_retries: int = 0
    total_time_ms: float = 0.0
    estimated_prompt_tokens: int = 0
    estimated_completion_tokens: int = 0
    cost_usd: float = 0.0  # $0.00 in 100% free mode


class IngestResponse(BaseModel):
    """Payload returned by POST /api/v1/documents/ingest."""
    document_id: UUID
    filename: str
    file_size_bytes: int
    page_count: int
    total_chunks: int
    extraction: Optional[InvoiceExtractionSchema] = None
    extraction_validation_passed: bool = True
    telemetry: IngestTelemetry

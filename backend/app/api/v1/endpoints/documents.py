import logging
import time
from typing import List, Optional
from uuid import UUID
from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status
from sqlalchemy import select, func, delete
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.database import get_db
from app.models.document import Document, DocumentChunk, DocumentExtraction
from app.schemas.extraction import InvoiceExtractionSchema
from app.schemas.search import SearchRequest, SearchResponse
from app.schemas.telemetry import IngestResponse, IngestTelemetry
from app.services.chunking_service import chunking_service
from app.services.embedding_service import embedding_service
from app.services.extractor_service import extractor_service
from app.services.pdf_service import pdf_service
from app.services.rag_service import rag_service

logger = logging.getLogger("docuvault.api.documents")
router = APIRouter(prefix="/documents", tags=["Documents & RAG"])


@router.post(
    "/ingest",
    response_model=IngestResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Ingest PDF in-memory, extract structured data, generate embeddings, and persist.",
)
async def ingest_document(
    file: UploadFile = File(..., description="Multipart PDF document"),
    db: AsyncSession = Depends(get_db),
) -> IngestResponse:
    """
    Core Ingestion Pipeline (Track A + Track B):
    1. Zero-Disk In-Memory Processing: Streams raw bytes via UploadFile.file.read().
    2. PyMuPDF parsing: Extracts text and page coordinates in a background threadpool.
    3. Track A (Structured Extraction): LLM extraction with Pydantic reflection loop.
    4. Track B (Hybrid RAG): Recursive character chunking + local FastEmbed embeddings (384d).
    5. Persistence: Writes Document, Chunks, and Extraction in a single ACID transaction.
    """
    total_start = time.perf_counter()
    telemetry = IngestTelemetry()

    # Guardrail: Verify file is a PDF
    if not file.filename.lower().endswith(".pdf") and file.content_type != "application/pdf":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid file format. Only PDF files are supported.",
        )

    # 1. Read directly into memory (zero disk I/O)
    file_bytes = await file.read()
    file_size_bytes = len(file_bytes)
    
    if file_size_bytes == 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="The uploaded PDF file is empty (0 bytes).",
        )

    # 2. In-Memory PDF Parsing via PyMuPDF
    parse_start = time.perf_counter()
    full_text, pages_data, page_count, content_hash = await pdf_service.extract_pdf_in_memory(file_bytes)
    telemetry.parse_time_ms = round((time.perf_counter() - parse_start) * 1000.0, 2)

    if not full_text.strip():
        logger.warning("PDF has no extractable text layer: %s", file.filename)
        full_text = f"Scanned or empty document: {file.filename}"

    # 3. Track A: Structured Extraction with Reflection Loop
    extract_start = time.perf_counter()
    extraction, retries_used, extract_ms, validation_passed = await extractor_service.extract_structured_data(
        full_text
    )
    telemetry.extraction_time_ms = round(extract_ms, 2)
    telemetry.extraction_retries = retries_used

    # 4. Track B: Chunking & Embedding Generation
    chunk_start = time.perf_counter()
    raw_chunks = await chunking_service.split_document_pages(pages_data)
    telemetry.chunk_time_ms = round((time.perf_counter() - chunk_start) * 1000.0, 2)

    embed_start = time.perf_counter()
    chunk_texts = [c["content"] for c in raw_chunks]
    embeddings = await embedding_service.generate_embeddings(chunk_texts)
    telemetry.embedding_time_ms = round((time.perf_counter() - embed_start) * 1000.0, 2)

    # 5. Database Persistence in Single ACID Transaction
    db_document = Document(
        filename=file.filename,
        file_size_bytes=file_size_bytes,
        page_count=page_count,
        content_hash=content_hash,
        status="processed",
    )
    db.add(db_document)
    await db.flush()  # Populates db_document.id

    # Create chunk records with vector embeddings
    db_chunks = []
    for idx, chunk_data in enumerate(raw_chunks):
        embedding_vector = embeddings[idx] if idx < len(embeddings) else None
        chunk_obj = DocumentChunk(
            document_id=db_document.id,
            chunk_index=chunk_data["chunk_index"],
            page_number=chunk_data["page_number"],
            content=chunk_data["content"],
            token_count=chunk_data["token_count"],
            embedding=embedding_vector,
        )
        db_chunks.append(chunk_obj)

    db.add_all(db_chunks)

    # Save extraction snapshot
    db_extraction = DocumentExtraction(
        document_id=db_document.id,
        schema_type="invoice",
        extracted_data=extraction.model_dump(),
        validation_passed=validation_passed,
        retry_count=retries_used,
        latency_ms=extract_ms,
    )
    db.add(db_extraction)

    await db.commit()
    await db.refresh(db_document)

    telemetry.total_time_ms = round((time.perf_counter() - total_start) * 1000.0, 2)
    telemetry.estimated_prompt_tokens = len(full_text.split())
    telemetry.estimated_completion_tokens = len(str(extraction.model_dump()).split())
    telemetry.cost_usd = 0.0  # 100% Free

    logger.info(
        "Ingested document '%s' (UUID: %s) with %d chunks in %.2f ms",
        file.filename,
        db_document.id,
        len(db_chunks),
        telemetry.total_time_ms,
    )

    return IngestResponse(
        document_id=db_document.id,
        filename=db_document.filename,
        file_size_bytes=db_document.file_size_bytes,
        page_count=db_document.page_count,
        total_chunks=len(db_chunks),
        extraction=extraction,
        extraction_validation_passed=validation_passed,
        telemetry=telemetry,
    )


@router.post(
    "/search",
    response_model=SearchResponse,
    summary="Execute Hybrid RAG search (Vector Cosine + Keyword FTS + RRF + FlashRank).",
)
async def search_documents(
    payload: SearchRequest,
    db: AsyncSession = Depends(get_db),
) -> SearchResponse:
    """
    Track B: Hybrid Search API
    Executes dense pgvector Cosine similarity + sparse Full-Text Search,
    merges using Reciprocal Rank Fusion (RRF), and applies the local Cross-Encoder reranker.
    """
    return await rag_service.execute_search(
        db=db,
        query=payload.query,
        mode=payload.mode,
        document_id=payload.document_id,
        top_k=payload.top_k,
        rerank=payload.rerank,
    )


@router.get(
    "",
    summary="List all ingested documents with page and chunk metrics.",
)
async def list_documents(
    skip: int = 0,
    limit: int = 50,
    db: AsyncSession = Depends(get_db),
):
    """Returns a list of all documents currently ingested in DocuVault AI."""
    stmt = (
        select(
            Document.id,
            Document.filename,
            Document.file_size_bytes,
            Document.page_count,
            Document.status,
            Document.created_at,
            func.count(DocumentChunk.id).label("total_chunks"),
        )
        .outerjoin(DocumentChunk, Document.id == DocumentChunk.document_id)
        .group_by(Document.id)
        .order_by(Document.created_at.desc())
        .offset(skip)
        .limit(limit)
    )
    result = await db.execute(stmt)
    rows = result.fetchall()

    return [
        {
            "id": row.id,
            "filename": row.filename,
            "file_size_bytes": row.file_size_bytes,
            "page_count": row.page_count,
            "status": row.status,
            "created_at": row.created_at,
            "total_chunks": row.total_chunks,
        }
        for row in rows
    ]


@router.get(
    "/{document_id}",
    summary="Get document details, chunks, and Pydantic extraction record.",
)
async def get_document_detail(
    document_id: UUID,
    db: AsyncSession = Depends(get_db),
):
    """Retrieves complete document metadata, extraction details, and preview chunks."""
    stmt = (
        select(Document)
        .where(Document.id == document_id)
        .options(
            selectinload(Document.extractions),
            selectinload(Document.chunks),
        )
    )
    result = await db.execute(stmt)
    document = result.scalar_one_or_none()

    if not document:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Document with ID {document_id} not found.",
        )

    latest_extraction = document.extractions[0] if document.extractions else None

    return {
        "id": document.id,
        "filename": document.filename,
        "file_size_bytes": document.file_size_bytes,
        "page_count": document.page_count,
        "created_at": document.created_at,
        "total_chunks": len(document.chunks),
        "extraction": latest_extraction.extracted_data if latest_extraction else None,
        "validation_passed": latest_extraction.validation_passed if latest_extraction else True,
        "retry_count": latest_extraction.retry_count if latest_extraction else 0,
        "extraction_latency_ms": latest_extraction.latency_ms if latest_extraction else 0.0,
    }


@router.delete(
    "/{document_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete a document and cascade its chunks and extractions.",
)
async def delete_document(
    document_id: UUID,
    db: AsyncSession = Depends(get_db),
):
    """Permanently deletes a document and all related vector chunks."""
    stmt = delete(Document).where(Document.id == document_id)
    result = await db.execute(stmt)
    if result.rowcount == 0:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Document with ID {document_id} not found.",
        )
    await db.commit()

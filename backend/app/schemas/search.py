from enum import Enum
from typing import List, Optional
from uuid import UUID
from pydantic import BaseModel, Field


class SearchMode(str, Enum):
    """Supported retrieval search modes."""
    HYBRID = "hybrid"
    VECTOR = "vector"
    KEYWORD = "keyword"


class SearchRequest(BaseModel):
    """Payload for POST /api/v1/documents/search."""
    query: str = Field(min_length=1, max_length=1000, description="User search query or question")
    mode: SearchMode = Field(default=SearchMode.HYBRID, description="Retrieval mode: hybrid, vector, or keyword")
    document_id: Optional[UUID] = Field(default=None, description="Filter search to a specific document UUID")
    top_k: int = Field(default=5, ge=1, le=50, description="Number of final results to return")
    rerank: bool = Field(default=True, description="Whether to apply the Cross-Encoder reranker")


class ChunkSearchResult(BaseModel):
    """Represents a single ranked retrieved document chunk with citations and multi-stage scores."""
    chunk_id: UUID
    document_id: UUID
    filename: str
    page_number: int
    chunk_index: int
    content: str
    
    # Retrieval Scores for Debugging in Frontend
    vector_score: Optional[float] = Field(default=None, description="Dense Cosine similarity score [0..1]")
    keyword_score: Optional[float] = Field(default=None, description="PostgreSQL Full-Text Search ts_rank_cd score")
    rrf_score: Optional[float] = Field(default=None, description="Reciprocal Rank Fusion composite score")
    rerank_score: Optional[float] = Field(default=None, description="Cross-Encoder relevance score [0..1]")
    final_rank: int = Field(description="Final ordinal position in the response")


class SearchTelemetry(BaseModel):
    """Fine-grained latency metrics for search execution stages."""
    dense_time_ms: float = 0.0
    sparse_time_ms: float = 0.0
    rrf_time_ms: float = 0.0
    rerank_time_ms: float = 0.0
    total_time_ms: float = 0.0


class SearchResponse(BaseModel):
    """Complete response payload for POST /api/v1/documents/search."""
    query: str
    mode: SearchMode
    rerank_applied: bool
    total_candidates_retrieved: int
    results: List[ChunkSearchResult]
    telemetry: SearchTelemetry

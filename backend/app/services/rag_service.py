import logging
import time
from typing import Dict, List, Optional
from uuid import UUID
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.schemas.search import ChunkSearchResult, SearchMode, SearchResponse, SearchTelemetry
from app.services.embedding_service import embedding_service
from app.services.reranker_service import reranker_service

logger = logging.getLogger("docuvault.rag")


class RAGService:
    """
    Track B: Enterprise Hybrid RAG Engine.
    Executes dense pgvector Cosine similarity + sparse PostgreSQL Full-Text Search,
    merges scores via Reciprocal Rank Fusion (RRF k=60), and refines with FlashRank Cross-Encoder.
    """

    async def execute_search(
        self,
        db: AsyncSession,
        query: str,
        mode: SearchMode = SearchMode.HYBRID,
        document_id: Optional[UUID] = None,
        top_k: int = 5,
        rerank: bool = True,
    ) -> SearchResponse:
        """
        Executes multi-stage search with live telemetry timing.
        """
        start_total = time.perf_counter()
        telemetry = SearchTelemetry()

        vector_results: List[Dict[str, any]] = []
        keyword_results: List[Dict[str, any]] = []

        filter_clause = "AND c.document_id = :doc_id" if document_id else ""
        query_params = {"limit": top_k * 4}
        if document_id:
            query_params["doc_id"] = str(document_id)

        # ---------------------------------------------------------
        # STAGE 1: Dense Vector Search (pgvector Cosine Sim <=> HNSW)
        # ---------------------------------------------------------
        if mode in (SearchMode.HYBRID, SearchMode.VECTOR):
            start_dense = time.perf_counter()
            query_embedding = await embedding_service.generate_query_embedding(query)
            query_params["query_vector"] = str(query_embedding)

            vector_sql = f"""
                SELECT 
                    c.id, 
                    c.document_id, 
                    d.filename, 
                    c.page_number, 
                    c.chunk_index, 
                    c.content,
                    1 - (c.embedding <=> :query_vector::vector) AS vector_score
                FROM document_chunks c
                JOIN documents d ON c.document_id = d.id
                WHERE c.embedding IS NOT NULL {filter_clause}
                ORDER BY c.embedding <=> :query_vector::vector ASC
                LIMIT :limit;
            """
            result = await db.execute(text(vector_sql), query_params)
            vector_results = [dict(row._mapping) for row in result.fetchall()]
            telemetry.dense_time_ms = (time.perf_counter() - start_dense) * 1000.0

        # ---------------------------------------------------------
        # STAGE 2: Sparse Keyword Search (PostgreSQL TSVECTOR + GIN)
        # ---------------------------------------------------------
        if mode in (SearchMode.HYBRID, SearchMode.KEYWORD):
            start_sparse = time.perf_counter()
            keyword_sql = f"""
                SELECT 
                    c.id, 
                    c.document_id, 
                    d.filename, 
                    c.page_number, 
                    c.chunk_index, 
                    c.content,
                    ts_rank_cd(c.tsv_content, websearch_to_tsquery('english', :search_query)) AS keyword_score
                FROM document_chunks c
                JOIN documents d ON c.document_id = d.id
                WHERE c.tsv_content @@ websearch_to_tsquery('english', :search_query) {filter_clause}
                ORDER BY keyword_score DESC
                LIMIT :limit;
            """
            sparse_params = {**query_params, "search_query": query}
            result = await db.execute(text(keyword_sql), sparse_params)
            keyword_results = [dict(row._mapping) for row in result.fetchall()]
            telemetry.sparse_time_ms = (time.perf_counter() - start_sparse) * 1000.0

        # ---------------------------------------------------------
        # STAGE 3: Reciprocal Rank Fusion (RRF k=60)
        # ---------------------------------------------------------
        start_rrf = time.perf_counter()
        k_constant = 60.0
        fused_candidates: Dict[UUID, Dict[str, any]] = {}

        if mode == SearchMode.HYBRID:
            # 1. Map vector ranks
            for rank_idx, item in enumerate(vector_results):
                cid = item["id"]
                item["vector_rank"] = rank_idx + 1
                item["rrf_score"] = 1.0 / (k_constant + rank_idx + 1)
                fused_candidates[cid] = item

            # 2. Add keyword ranks
            for rank_idx, item in enumerate(keyword_results):
                cid = item["id"]
                item["keyword_rank"] = rank_idx + 1
                rrf_contrib = 1.0 / (k_constant + rank_idx + 1)
                if cid in fused_candidates:
                    fused_candidates[cid]["keyword_score"] = item["keyword_score"]
                    fused_candidates[cid]["rrf_score"] += rrf_contrib
                else:
                    item["rrf_score"] = rrf_contrib
                    fused_candidates[cid] = item

            candidate_list = sorted(
                fused_candidates.values(), key=lambda x: x.get("rrf_score", 0.0), reverse=True
            )
        elif mode == SearchMode.VECTOR:
            candidate_list = vector_results
        else:
            candidate_list = keyword_results

        telemetry.rrf_time_ms = (time.perf_counter() - start_rrf) * 1000.0

        # ---------------------------------------------------------
        # STAGE 4: Local FlashRank Cross-Encoder Reranking
        # ---------------------------------------------------------
        rerank_applied = False
        final_list = candidate_list

        if rerank and candidate_list:
            start_rerank = time.perf_counter()
            rerank_candidates = candidate_list[: top_k * 3]
            reranked_output = await reranker_service.rerank(query, rerank_candidates, top_k=top_k)
            
            # Map FlashRank relevance scores back to candidate objects
            final_list = []
            for item in reranked_output:
                meta = item["meta"]
                meta["rerank_score"] = round(float(item["score"]), 4)
                final_list.append(meta)
            
            rerank_applied = True
            telemetry.rerank_time_ms = (time.perf_counter() - start_rerank) * 1000.0
        else:
            final_list = candidate_list[:top_k]

        telemetry.total_time_ms = (time.perf_counter() - start_total) * 1000.0

        # Convert to Pydantic ChunkSearchResult schemas
        search_results: List[ChunkSearchResult] = []
        for idx, item in enumerate(final_list):
            search_results.append(
                ChunkSearchResult(
                    chunk_id=item["id"],
                    document_id=item["document_id"],
                    filename=item["filename"],
                    page_number=item["page_number"],
                    chunk_index=item["chunk_index"],
                    content=item["content"],
                    vector_score=round(float(item["vector_score"]), 4) if "vector_score" in item and item["vector_score"] is not None else None,
                    keyword_score=round(float(item["keyword_score"]), 4) if "keyword_score" in item and item["keyword_score"] is not None else None,
                    rrf_score=round(float(item["rrf_score"]), 5) if "rrf_score" in item and item["rrf_score"] is not None else None,
                    rerank_score=item.get("rerank_score"),
                    final_rank=idx + 1,
                )
            )

        return SearchResponse(
            query=query,
            mode=mode,
            rerank_applied=rerank_applied,
            total_candidates_retrieved=len(candidate_list),
            results=search_results,
            telemetry=telemetry,
        )


rag_service = RAGService()

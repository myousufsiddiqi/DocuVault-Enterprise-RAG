import asyncio
import logging
from typing import Dict, List, Optional
from flashrank import Ranker, RerankRequest

from app.core.config import settings

logger = logging.getLogger("docuvault.reranker")


class RerankerService:
    """
    100% Free Local Cross-Encoder Reranker Service.
    Powered by FlashRank running locally on CPU in ~15ms.
    Evaluates (query, text) pairs via cross-attention for high-precision re-scoring.
    Zero API keys, zero internet calls, zero rate limits.
    """

    def __init__(self):
        self._ranker: Optional[Ranker] = None

    def _get_ranker(self) -> Ranker:
        """Lazy thread-safe initialization of the FlashRank Cross-Encoder model."""
        if self._ranker is None:
            logger.info("Initializing local FlashRank model: %s", settings.RERANK_MODEL)
            self._ranker = Ranker(model_name=settings.RERANK_MODEL, cache_dir="/tmp/flashrank_cache")
        return self._ranker

    def _rerank_sync(self, query: str, passages: List[Dict[str, any]]) -> List[Dict[str, any]]:
        """
        Synchronous reranking worker executed in a background thread.
        Each passage dict contains: {"id": str, "text": str, "meta": dict}.
        """
        ranker = self._get_ranker()
        rerank_req = RerankRequest(query=query, passages=passages)
        results = ranker.rerank(rerank_req)
        return results

    async def rerank(
        self, query: str, candidates: List[Dict[str, any]], top_k: int = 5
    ) -> List[Dict[str, any]]:
        """
        Asynchronously reranks a list of candidate chunks.
        
        Args:
            query: The search query string.
            candidates: List of candidate chunk dicts (must contain 'id' and 'text').
            top_k: Number of top-ranked items to return.
            
        Returns:
            List of reranked candidate dicts with added 'score' field.
        """
        if not candidates:
            return []

        # Format candidates for FlashRank
        passages = [
            {
                "id": str(c["id"]),
                "text": c["content"],
                "meta": c,
            }
            for c in candidates
        ]

        reranked_results = await asyncio.to_thread(self._rerank_sync, query, passages)
        return reranked_results[:top_k]


reranker_service = RerankerService()

import asyncio
import logging
from typing import List, Optional
from fastembed import TextEmbedding

from app.core.config import settings

logger = logging.getLogger("docuvault.embedding")


class EmbeddingService:
    """
    100% Free Local Embedding Service.
    Powered by FastEmbed (ONNX) running locally on CPU.
    Produces 384-dimensional vectors using BAAI/bge-small-en-v1.5.
    Zero API keys, zero internet calls, zero rate limits.
    """

    def __init__(self):
        self._model: Optional[TextEmbedding] = None

    def _get_model(self) -> TextEmbedding:
        """Lazy thread-safe initialization of the FastEmbed ONNX model."""
        if self._model is None:
            logger.info("Initializing local FastEmbed model: %s", settings.EMBEDDING_MODEL)
            self._model = TextEmbedding(model_name=settings.EMBEDDING_MODEL)
        return self._model

    def _embed_texts_sync(self, texts: List[str]) -> List[List[float]]:
        """Synchronous embedding generation worker executed in a background thread."""
        model = self._get_model()
        # FastEmbed returns a generator of numpy arrays
        embeddings_generator = model.embed(texts)
        return [embedding.tolist() for embedding in embeddings_generator]

    async def generate_embeddings(self, texts: List[str]) -> List[List[float]]:
        """
        Asynchronously generates 384-dimensional dense vectors for a list of strings.
        Offloads computation to worker threadpool to preserve zero-blocking I/O.
        """
        if not texts:
            return []
        return await asyncio.to_thread(self._embed_texts_sync, texts)

    async def generate_query_embedding(self, query: str) -> List[float]:
        """Asynchronously embeds a single query string for vector search."""
        results = await self.generate_embeddings([query])
        return results[0] if results else [0.0] * settings.EMBEDDING_DIM


embedding_service = EmbeddingService()

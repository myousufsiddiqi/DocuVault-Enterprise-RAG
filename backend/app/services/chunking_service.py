import asyncio
from typing import Dict, List
from langchain_text_splitters import RecursiveCharacterTextSplitter


class ChunkingService:
    """
    Semantic chunking service powered by LangChain's RecursiveCharacterTextSplitter.
    Respects document boundaries, paragraph markers, and sentence delimiters.
    """

    def __init__(self, chunk_size: int = 800, chunk_overlap: int = 150):
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        self.splitter = RecursiveCharacterTextSplitter(
            chunk_size=self.chunk_size,
            chunk_overlap=self.chunk_overlap,
            separators=["\n\n", "\n", ". ", " ", ""],
            length_function=len,
        )

    def _split_pages_sync(self, pages_data: List[Dict[str, any]]) -> List[Dict[str, any]]:
        """
        Synchronous worker method executing inside the worker threadpool.
        Splits text page-by-page to retain accurate page citations.
        """
        all_chunks: List[Dict[str, any]] = []
        global_chunk_idx = 0

        for page in pages_data:
            page_num = page["page_number"]
            page_text = page["text"]

            if not page_text:
                continue

            split_texts = self.splitter.split_text(page_text)
            for text_chunk in split_texts:
                cleaned_text = text_chunk.strip()
                if cleaned_text:
                    all_chunks.append({
                        "chunk_index": global_chunk_idx,
                        "page_number": page_num,
                        "content": cleaned_text,
                        "token_count": len(cleaned_text.split()),
                    })
                    global_chunk_idx += 1

        return all_chunks

    async def split_document_pages(
        self, pages_data: List[Dict[str, any]]
    ) -> List[Dict[str, any]]:
        """Asynchronously chunks extracted pages without blocking the event loop."""
        return await asyncio.to_thread(self._split_pages_sync, pages_data)


chunking_service = ChunkingService()

import asyncio
import hashlib
from typing import Dict, List, Tuple
import fitz  # PyMuPDF


class PDFService:
    """
    In-memory PDF Ingestion Service.
    Enforces the zero-disk-I/O guardrail: uploaded bytes stream directly into PyMuPDF.
    CPU-bound parsing operations are offloaded to an asynchronous threadpool.
    """

    @staticmethod
    def _parse_bytes_sync(file_bytes: bytes) -> Tuple[str, List[Dict[str, any]], int, str]:
        """
        Synchronous worker method executed inside asyncio.to_thread.
        Extracts raw text, per-page content, and computes SHA-256 content hash.
        """
        # Read directly from in-memory byte buffer
        doc = fitz.open(stream=file_bytes, filetype="pdf")
        total_pages = doc.page_count
        pages_data: List[Dict[str, any]] = []
        full_text_parts: List[str] = []

        for page_idx in range(total_pages):
            page = doc.load_page(page_idx)
            page_text = page.get_text("text").strip()
            pages_data.append({
                "page_number": page_idx + 1,
                "text": page_text,
                "char_count": len(page_text),
            })
            if page_text:
                full_text_parts.append(page_text)

        doc.close()

        full_text = "\n\n".join(full_text_parts)
        content_hash = hashlib.sha256(file_bytes).hexdigest()

        return full_text, pages_data, total_pages, content_hash

    async def extract_pdf_in_memory(
        self, file_bytes: bytes
    ) -> Tuple[str, List[Dict[str, any]], int, str]:
        """
        Asynchronously parses an in-memory PDF without blocking the event loop.
        
        Returns:
            Tuple of:
            - full_text (str): All concatenated text.
            - pages_data (List[dict]): Page-by-page text and metadata.
            - page_count (int): Total number of pages.
            - content_hash (str): SHA-256 fingerprint for deduplication.
        """
        return await asyncio.to_thread(self._parse_bytes_sync, file_bytes)


pdf_service = PDFService()

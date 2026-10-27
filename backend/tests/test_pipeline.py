import asyncio
import io
import fitz  # PyMuPDF
from app.schemas.extraction import LineItemSchema, InvoiceExtractionSchema
from app.services.chunking_service import chunking_service
from app.services.pdf_service import pdf_service


def test_pydantic_arithmetic_validation_pass():
    """Verifies that balanced line items and subtotals pass Pydantic validation."""
    valid_invoice = InvoiceExtractionSchema(
        invoice_number="INV-2026-001",
        invoice_date="2026-10-25",
        vendor_name="Acme Corp",
        customer_name="Globex Inc",
        line_items=[
            LineItemSchema(description="Cloud Servers", quantity=2.0, unit_price=50.0, total=100.0),
            LineItemSchema(description="Database Storage", quantity=1.0, unit_price=150.0, total=150.0),
        ],
        subtotal=250.0,
        tax_amount=25.0,
        discount_amount=0.0,
        grand_total=275.0,
    )
    assert valid_invoice.subtotal == 250.0
    assert valid_invoice.grand_total == 275.0
    print("[PASS] Valid invoice passed mathematical reflection check.")


def test_pydantic_arithmetic_validation_fail_triggers_reflection():
    """Verifies that an arithmetic discrepancy raises ValueError for the reflection loop."""
    try:
        # Deliberate hallucination: 100 + 150 != 300
        InvoiceExtractionSchema(
            invoice_number="INV-BAD-MATH",
            invoice_date="2026-10-25",
            vendor_name="Buggy Vendor",
            customer_name="Client",
            line_items=[
                LineItemSchema(description="Item 1", quantity=1.0, unit_price=100.0, total=100.0),
                LineItemSchema(description="Item 2", quantity=1.0, unit_price=150.0, total=150.0),
            ],
            subtotal=300.0,  # Wrong! Should be 250.0
            tax_amount=0.0,
            discount_amount=0.0,
            grand_total=300.0,
        )
        assert False, "Should have raised ValueError on subtotal mismatch!"
    except ValueError as e:
        assert "Subtotal Arithmetic Mismatch" in str(e)
        print("[PASS] Arithmetic mismatch correctly caught by Pydantic reflection validator:", str(e))


async def test_in_memory_pdf_and_chunking():
    """Verifies end-to-end in-memory PDF creation and chunking without disk I/O."""
    # 1. Create a synthetic PDF entirely in RAM
    doc = fitz.open()
    page1 = doc.new_page()
    page1.insert_text((50, 72), "DocuVault AI Invoice Test Document. Page 1 content with enterprise terms.")
    page2 = doc.new_page()
    page2.insert_text((50, 72), "Page 2 content: Line items summary and payment terms for Hybrid RAG retrieval.")
    
    pdf_bytes = doc.tobytes()
    doc.close()

    # 2. Ingest via PDFService in-memory
    full_text, pages_data, page_count, content_hash = await pdf_service.extract_pdf_in_memory(pdf_bytes)
    assert page_count == 2
    assert "DocuVault AI Invoice" in full_text
    assert len(content_hash) == 64
    print("[PASS] In-memory PDF streaming parsed 2 pages without disk I/O.")

    # 3. Chunk text via ChunkingService
    chunks = await chunking_service.split_document_pages(pages_data)
    assert len(chunks) >= 2
    assert chunks[0]["page_number"] == 1
    assert chunks[1]["page_number"] == 2
    print(f"[PASS] Semantic chunking created {len(chunks)} chunks with accurate page citations.")


if __name__ == "__main__":
    print("--- Running DocuVault AI Foundational Unit Tests ---")
    test_pydantic_arithmetic_validation_pass()
    test_pydantic_arithmetic_validation_fail_triggers_reflection()
    asyncio.run(test_in_memory_pdf_and_chunking())
    print("--- All Unit Tests Passed Successfully ---")

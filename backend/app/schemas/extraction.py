from typing import List, Optional
from pydantic import BaseModel, Field, model_validator


class LineItemSchema(BaseModel):
    """Represents a single purchased item or billed service in a document."""
    description: str = Field(description="Description of the goods or services provided")
    quantity: float = Field(default=1.0, description="Quantity or hours billed")
    unit_price: float = Field(description="Unit price or rate per item")
    total: float = Field(description="Total line item cost before tax")

    @model_validator(mode="after")
    def validate_line_total(self) -> "LineItemSchema":
        """Mathematically verifies that quantity * unit_price equals total."""
        expected_total = round(self.quantity * self.unit_price, 2)
        actual_total = round(self.total, 2)
        # 5 cent tolerance for rounding variances
        if abs(expected_total - actual_total) > 0.05:
            raise ValueError(
                f"Line item '{self.description}' arithmetic mismatch: "
                f"quantity ({self.quantity}) * unit_price ({self.unit_price:.2f}) = {expected_total:.2f}, "
                f"but extracted total is {actual_total:.2f}. Discrepancy: {abs(expected_total - actual_total):.2f}"
            )
        return self


class InvoiceExtractionSchema(BaseModel):
    """
    Enterprise Structured Document Schema (Track A).
    Enforces strict relational contracts and mathematical validation reflection loops.
    """
    invoice_number: str = Field(description="Unique invoice, statement, or contract identifier")
    invoice_date: str = Field(description="Date of invoice issuance (YYYY-MM-DD or as stated)")
    due_date: Optional[str] = Field(default=None, description="Due date for payment if stated")
    vendor_name: str = Field(description="Name of the billing company, vendor, or supplier")
    vendor_address: Optional[str] = Field(default=None, description="Vendor street or mailing address")
    customer_name: str = Field(description="Name of the billed customer or receiving organization")
    customer_address: Optional[str] = Field(default=None, description="Customer street or mailing address")
    
    line_items: List[LineItemSchema] = Field(
        default_factory=list, description="List of individual line items extracted from the document"
    )
    
    subtotal: float = Field(description="Subtotal amount before taxes, fees, and discounts")
    tax_amount: float = Field(default=0.0, description="Total sales tax, VAT, or duties applied")
    discount_amount: float = Field(default=0.0, description="Total discount subtracted, if applicable")
    grand_total: float = Field(description="Final payable invoice balance or grand total")
    currency: str = Field(default="USD", description="Currency ISO code or symbol (e.g. USD, EUR, $)")

    @model_validator(mode="after")
    def validate_totals_math(self) -> "InvoiceExtractionSchema":
        """
        Critical Engineering Guardrail:
        Mathematically audits the LLM's output. If arithmetic discrepancies exist,
        raises a detailed ValueError that will be fed directly back into the LLM reflection loop.
        """
        # 1. Audit line-item aggregation
        if self.line_items:
            calculated_subtotal = round(sum(item.total for item in self.line_items), 2)
            actual_subtotal = round(self.subtotal, 2)
            if abs(calculated_subtotal - actual_subtotal) > 0.10:
                raise ValueError(
                    f"Subtotal Arithmetic Mismatch: The sum of line-item totals is "
                    f"${calculated_subtotal:.2f}, but the extracted subtotal is ${actual_subtotal:.2f}. "
                    f"Discrepancy: ${abs(calculated_subtotal - actual_subtotal):.2f}. "
                    f"Please review line-item totals or subtotal."
                )

        # 2. Audit grand total math (subtotal + tax - discount == grand_total)
        expected_grand_total = round(self.subtotal + self.tax_amount - self.discount_amount, 2)
        actual_grand_total = round(self.grand_total, 2)
        if abs(expected_grand_total - actual_grand_total) > 0.10:
            raise ValueError(
                f"Grand Total Arithmetic Mismatch: Subtotal (${self.subtotal:.2f}) + "
                f"Tax (${self.tax_amount:.2f}) - Discount (${self.discount_amount:.2f}) = "
                f"${expected_grand_total:.2f}, but the extracted grand_total is ${actual_grand_total:.2f}. "
                f"Discrepancy: ${abs(expected_grand_total - actual_grand_total):.2f}."
            )

        return self

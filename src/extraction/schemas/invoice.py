from pydantic import BaseModel, Field
from typing import Optional


class InvoiceLineItem(BaseModel):
    item_number: Optional[str] = Field(None, description="Line item number")
    description: Optional[str] = Field(None, description="Service or product description")
    quantity: Optional[str] = Field(None, description="Quantity billed")
    unit: Optional[str] = Field(None, description="Unit of measure")
    unit_price: Optional[str] = Field(None, description="Price per unit")
    extended_price: Optional[str] = Field(None, description="Line total before taxes")


class InvoiceResult(BaseModel):
    invoice_number: Optional[str] = Field(None, description="Invoice reference number")
    invoice_date: Optional[str] = Field(None, description="Date the invoice was issued, NOT the due date")
    due_date: Optional[str] = Field(None, description="Payment due date, NOT the invoice date")
    issuer_name: Optional[str] = Field(None, description="Name of the company issuing the invoice")
    issuer_address: Optional[str] = Field(None, description="Address of the invoice issuer")
    recipient_name: Optional[str] = Field(None, description="Name of the bill-to party")
    recipient_address: Optional[str] = Field(None, description="Address of the recipient")
    currency: Optional[str] = Field(None, description="Currency code or symbol")
    subtotal: Optional[str] = Field(None, description="Pre-tax subtotal amount")
    tax_total: Optional[str] = Field(None, description="Total tax or VAT amount")
    total_amount: Optional[str] = Field(None, description="Grand total including taxes")
    payment_terms: Optional[str] = Field(None, description="Payment terms (e.g., Net 30)")
    po_reference: Optional[str] = Field(None, description="Purchase order number this invoice relates to, if present")
    line_items: list[InvoiceLineItem] = Field(default_factory=list, description="List of billed line items")

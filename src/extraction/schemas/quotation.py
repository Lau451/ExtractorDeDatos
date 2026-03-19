from pydantic import BaseModel, Field
from typing import Optional


class QuotationResult(BaseModel):
    quote_number: Optional[str] = Field(None, description="Quotation reference number")
    quote_date: Optional[str] = Field(None, description="Date the quotation was issued")
    vendor_name: Optional[str] = Field(None, description="Vendor or supplier issuing the quotation")
    vendor_address: Optional[str] = Field(None, description="Vendor contact address")
    buyer_name: Optional[str] = Field(None, description="Buyer or customer the quote is addressed to")
    valid_until: Optional[str] = Field(None, description="Expiry date of the quotation")
    currency: Optional[str] = Field(None, description="Currency of the quoted prices")
    subtotal: Optional[str] = Field(None, description="Pre-tax subtotal")
    tax_total: Optional[str] = Field(None, description="Total tax amount")
    grand_total: Optional[str] = Field(None, description="Total amount including taxes")
    payment_terms: Optional[str] = Field(None, description="Payment terms (e.g., Net 30)")
    delivery_terms: Optional[str] = Field(None, description="Delivery or Incoterms specification")

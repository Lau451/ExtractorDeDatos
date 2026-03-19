from pydantic import BaseModel, Field
from typing import Optional


class SupplierRow(BaseModel):
    supplier_name: Optional[str] = Field(None, description="Name of the supplier or vendor being evaluated")
    item_description: Optional[str] = Field(None, description="Item or service being quoted by this supplier")
    unit_price: Optional[str] = Field(None, description="Price per unit quoted by this supplier")
    total_price: Optional[str] = Field(None, description="Total price for the required quantity")
    lead_time: Optional[str] = Field(None, description="Delivery lead time quoted")
    payment_terms: Optional[str] = Field(None, description="Payment terms offered by this supplier")
    delivery_terms: Optional[str] = Field(None, description="Delivery or Incoterms for this supplier")
    warranty: Optional[str] = Field(None, description="Warranty terms, if stated")
    compliance_notes: Optional[str] = Field(None, description="Compliance or certification notes")
    overall_score: Optional[str] = Field(None, description="Evaluation score or rank, if documented")


class SupplierComparisonResult(BaseModel):
    project_name: Optional[str] = Field(None, description="Name of the project or procurement being compared")
    comparison_date: Optional[str] = Field(None, description="Date the comparison was prepared")
    rfq_reference: Optional[str] = Field(None, description="RFQ or tender reference this comparison responds to")
    evaluation_criteria: Optional[str] = Field(None, description="Criteria used to evaluate suppliers (price, quality, etc.)")
    recommended_supplier: Optional[str] = Field(None, description="Overall recommended supplier, if documented")
    notes: Optional[str] = Field(None, description="Additional evaluation notes or context")
    line_items: list[SupplierRow] = Field(default_factory=list, description="One row per supplier evaluated")

from pydantic import BaseModel, Field
from typing import Optional


class TenderLineItem(BaseModel):
    item_number: Optional[str] = Field(None, description="Line item number or sequence number")
    quantity: Optional[str] = Field(None, description="Requested quantity as a string")
    description: Optional[str] = Field(None, description="Product name or item description")


class TenderRFQResult(BaseModel):
    tender_reference: Optional[str] = Field(None, description="Tender or RFQ reference number")
    issue_date: Optional[str] = Field(None, description="Date the tender was issued")
    issuing_organization: Optional[str] = Field(None, description="Organization issuing the tender")
    submission_deadline: Optional[str] = Field(None, description="Deadline for submitting responses")
    contact_person: Optional[str] = Field(None, description="Contact name for the tender")
    project_title: Optional[str] = Field(None, description="Project or scope title described in the tender")
    currency: Optional[str] = Field(None, description="Currency specified for bids")
    notes: Optional[str] = Field(None, description="Additional notes, conditions, or requirements")
    line_items: list[TenderLineItem] = Field(default_factory=list, description="List of requested line items")

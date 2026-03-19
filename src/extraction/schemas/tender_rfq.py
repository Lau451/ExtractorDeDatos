from pydantic import BaseModel, Field
from typing import Optional


class TenderRFQResult(BaseModel):
    tender_reference: Optional[str] = Field(None, description="Tender or RFQ reference number")
    issue_date: Optional[str] = Field(None, description="Date the tender was issued")
    issuing_organization: Optional[str] = Field(None, description="Organization issuing the tender")
    submission_deadline: Optional[str] = Field(None, description="Deadline for submitting responses")
    contact_person: Optional[str] = Field(None, description="Contact name for the tender")
    project_title: Optional[str] = Field(None, description="Project or scope title described in the tender")
    currency: Optional[str] = Field(None, description="Currency specified for bids")
    notes: Optional[str] = Field(None, description="Additional notes, conditions, or requirements")

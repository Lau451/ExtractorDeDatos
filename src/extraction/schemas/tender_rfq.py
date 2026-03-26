from pydantic import BaseModel, Field
from typing import Optional


class TenderLineItem(BaseModel):
    item_number: Optional[str] = Field(None, description="Line item number or sequence number")
    quantity: Optional[str] = Field(None, description="Requested quantity as a string")
    description: Optional[str] = Field(None, description="Product name or item description")


class TenderRFQResult(BaseModel):
    line_items: list[TenderLineItem] = Field(default_factory=list, description="List of requested line items")

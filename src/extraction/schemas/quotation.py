from pydantic import BaseModel, Field
from typing import Optional


class QuotationLineItem(BaseModel):
    item_number: Optional[str] = Field(None, description="Line item number or sequence number")
    quantity: Optional[str] = Field(None, description="Quoted quantity as a string")
    description: Optional[str] = Field(None, description="Product name or item description")


class QuotationResult(BaseModel):
    line_items: list[QuotationLineItem] = Field(default_factory=list, description="List of quoted line items")

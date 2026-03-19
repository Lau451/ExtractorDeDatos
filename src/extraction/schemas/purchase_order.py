from pydantic import BaseModel, Field
from typing import Optional


class POLineItem(BaseModel):
    item_number: Optional[str] = Field(None, description="Line item number or sequence number")
    description: Optional[str] = Field(None, description="Product name or item description")
    sku: Optional[str] = Field(None, description="SKU, part number, or item code")
    quantity: Optional[str] = Field(None, description="Ordered quantity as a string to preserve formatting")
    unit: Optional[str] = Field(None, description="Unit of measure (each, kg, box, etc.)")
    unit_price: Optional[str] = Field(None, description="Price per unit in the document currency")
    extended_price: Optional[str] = Field(None, description="Line total = quantity × unit price")


class PurchaseOrderResult(BaseModel):
    po_number: Optional[str] = Field(None, description="Purchase order reference number")
    issue_date: Optional[str] = Field(None, description="Date the PO was issued, in original format")
    buyer_name: Optional[str] = Field(None, description="Name of the buying organization or entity")
    supplier_name: Optional[str] = Field(None, description="Name of the supplier or vendor")
    delivery_date: Optional[str] = Field(None, description="Requested delivery or due date")
    currency: Optional[str] = Field(None, description="Currency code or symbol (e.g., USD, €)")
    total_amount: Optional[str] = Field(None, description="Grand total amount of the purchase order")
    payment_terms: Optional[str] = Field(None, description="Payment terms (e.g., Net 30, 2/10 Net 30)")
    shipping_address: Optional[str] = Field(None, description="Delivery address for the goods")
    notes: Optional[str] = Field(None, description="Additional notes or special instructions")
    line_items: list[POLineItem] = Field(default_factory=list, description="List of ordered line items")

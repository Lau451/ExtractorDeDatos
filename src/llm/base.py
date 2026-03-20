from typing import Protocol, runtime_checkable
from pydantic import BaseModel


@runtime_checkable
class LLMProvider(Protocol):
    async def classify(self, text: str) -> str:
        """Classify document text. Return one of: purchase_order, tender_rfq, quotation, invoice, supplier_comparison, unknown."""
        ...

    async def extract(self, text: str, schema: type[BaseModel]) -> BaseModel:
        """Extract structured fields from text using the given Pydantic schema."""
        ...

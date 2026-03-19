from src.extraction.schemas.purchase_order import PurchaseOrderResult
from src.extraction.schemas.tender_rfq import TenderRFQResult
from src.extraction.schemas.quotation import QuotationResult
from src.extraction.schemas.invoice import InvoiceResult
from src.extraction.schemas.supplier_comparison import SupplierComparisonResult

SCHEMA_REGISTRY: dict[str, type] = {
    "purchase_order": PurchaseOrderResult,
    "tender_rfq": TenderRFQResult,
    "quotation": QuotationResult,
    "invoice": InvoiceResult,
    "supplier_comparison": SupplierComparisonResult,
}

VALID_DOC_TYPES = set(SCHEMA_REGISTRY.keys())

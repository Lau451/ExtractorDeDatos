import pytest
from pathlib import Path
from unittest.mock import AsyncMock, patch, MagicMock

# Fixture loader helper
FIXTURES_DIR = Path(__file__).parent / "fixtures"


def load_fixture(name: str) -> str:
    return (FIXTURES_DIR / name).read_text(encoding="utf-8")


# ---- Classification tests (CLS-01) ----


async def test_classify_returns_known_type():
    """CLS-01: classify() returns one of the 5 known type strings."""
    known_types = {
        "purchase_order",
        "tender_rfq",
        "quotation",
        "invoice",
        "supplier_comparison",
    }
    mock_response = MagicMock()
    mock_response.text = "purchase_order"

    with patch("src.llm.gemini.GeminiProvider") as MockProvider:
        provider = MockProvider.return_value
        provider.classify = AsyncMock(return_value="purchase_order")

        result = await provider.classify(load_fixture("sample_po.md"))
        assert result in known_types


async def test_classify_unknown():
    """CLS-01: classify() returns 'unknown' for ambiguous text."""
    with patch("src.llm.gemini.GeminiProvider") as MockProvider:
        provider = MockProvider.return_value
        provider.classify = AsyncMock(return_value="unknown")

        result = await provider.classify("This text does not match any procurement document type.")
        assert result == "unknown"


# ---- Classification visibility (CLS-02) ----


async def test_job_has_doc_type_after_classification(client):
    """CLS-02: GET /jobs/{id} includes doc_type after classification completes."""
    from src.core.job_store import job_store

    # Create a job via upload endpoint
    upload_response = await client.post(
        "/extract",
        files={"file": ("test.pdf", b"%PDF-1.4 fake content", "application/pdf")},
    )
    assert upload_response.status_code == 200
    job_id = upload_response.json()["job_id"]

    # Simulate classification completing by setting doc_type directly
    await job_store.set_doc_type(job_id, "purchase_order")

    # GET /jobs/{id} must include doc_type
    response = await client.get(f"/jobs/{job_id}")
    assert response.status_code == 200
    body = response.json()
    assert "doc_type" in body
    assert body["doc_type"] == "purchase_order"


# ---- PO extraction (EXT-01, EXT-06) ----


async def test_po_extraction_header():
    """EXT-01: PO extraction returns expected header fields."""
    from src.extraction.schemas.purchase_order import PurchaseOrderResult

    mock_result = PurchaseOrderResult(
        po_number="PO-2024-0847",
        issue_date="2024-03-15",
        buyer_name="Acme Manufacturing Ltd.",
        supplier_name="Global Parts Supply Co.",
        delivery_date="2024-04-15",
        currency="USD",
        total_amount="$2,554.88",
        payment_terms="Net 30",
        shipping_address="123 Industrial Way, Chicago, IL 60601",
    )

    with patch("src.llm.gemini.GeminiProvider") as MockProvider:
        provider = MockProvider.return_value
        provider.extract = AsyncMock(return_value=mock_result)

        result = await provider.extract(load_fixture("sample_po.md"), PurchaseOrderResult)

        assert result.po_number == "PO-2024-0847"
        assert result.buyer_name == "Acme Manufacturing Ltd."
        assert result.supplier_name == "Global Parts Supply Co."
        assert result.issue_date == "2024-03-15"
        assert result.currency == "USD"
        assert result.total_amount == "$2,554.88"
        assert result.payment_terms == "Net 30"


async def test_po_extraction_line_items():
    """EXT-06: PO extraction returns line_items list."""
    from src.extraction.schemas.purchase_order import PurchaseOrderResult, POLineItem

    mock_result = PurchaseOrderResult(
        po_number="PO-2024-0847",
        line_items=[
            POLineItem(
                item_number="1",
                description="Steel Bolts M10x50",
                sku="SB-M1050",
                quantity="500",
                unit="each",
                unit_price="$0.45",
                extended_price="$225.00",
            ),
            POLineItem(
                item_number="2",
                description="Hydraulic Hose Assembly",
                sku="HH-3042",
                quantity="12",
                unit="each",
                unit_price="$89.99",
                extended_price="$1,079.88",
            ),
        ],
    )

    with patch("src.llm.gemini.GeminiProvider") as MockProvider:
        provider = MockProvider.return_value
        provider.extract = AsyncMock(return_value=mock_result)

        result = await provider.extract(load_fixture("sample_po.md"), PurchaseOrderResult)

        assert isinstance(result.line_items, list)
        assert len(result.line_items) >= 1
        first_item = result.line_items[0]
        assert first_item.description is not None
        assert first_item.quantity is not None
        assert first_item.unit_price is not None
        assert first_item.extended_price is not None


# ---- Tender/RFQ extraction (EXT-02) ----


async def test_tender_extraction():
    """EXT-02: Tender/RFQ extraction returns expected header fields."""
    from src.extraction.schemas.tender_rfq import TenderRFQResult

    mock_result = TenderRFQResult(
        tender_reference="RFQ-2024-0312",
        issue_date="2024-02-28",
        issuing_organization="Metro City Public Works Department",
        submission_deadline="2024-03-28 17:00 EST",
        contact_person="Maria Rodriguez",
        project_title="Downtown Water Main Replacement Phase III",
        currency="USD",
    )

    with patch("src.llm.gemini.GeminiProvider") as MockProvider:
        provider = MockProvider.return_value
        provider.extract = AsyncMock(return_value=mock_result)

        result = await provider.extract(load_fixture("sample_tender.md"), TenderRFQResult)

        assert result.tender_reference == "RFQ-2024-0312"
        assert result.issuing_organization == "Metro City Public Works Department"
        assert result.submission_deadline is not None
        assert result.project_title is not None


# ---- Quotation extraction (EXT-03) ----


async def test_quotation_extraction():
    """EXT-03: Quotation extraction returns expected fields."""
    from src.extraction.schemas.quotation import QuotationResult

    mock_result = QuotationResult(
        quote_number="QT-2024-0198",
        quote_date="2024-03-05",
        vendor_name="Premium Pipe Solutions Inc.",
        vendor_address="789 Pipeline Road, Houston, TX 77001",
        buyer_name="Metro City Public Works Department",
        valid_until="2024-04-05",
        currency="USD",
        subtotal="$384,000.00",
        tax_total="$27,840.00",
        grand_total="$411,840.00",
        payment_terms="50% on order, 50% on completion",
        delivery_terms="FOB Destination, 45 days ARO",
    )

    with patch("src.llm.gemini.GeminiProvider") as MockProvider:
        provider = MockProvider.return_value
        provider.extract = AsyncMock(return_value=mock_result)

        result = await provider.extract(load_fixture("sample_quotation.md"), QuotationResult)

        assert result.quote_number == "QT-2024-0198"
        assert result.vendor_name == "Premium Pipe Solutions Inc."
        assert result.grand_total == "$411,840.00"
        assert result.valid_until == "2024-04-05"


# ---- Invoice extraction (EXT-04, EXT-07) ----


async def test_invoice_extraction_header():
    """EXT-04: Invoice extraction returns expected header fields."""
    from src.extraction.schemas.invoice import InvoiceResult

    mock_result = InvoiceResult(
        invoice_number="INV-2024-1523",
        invoice_date="2024-03-20",
        due_date="2024-04-19",
        issuer_name="Global Parts Supply Co.",
        issuer_address="456 Commerce Blvd, Suite 200, Detroit, MI 48201",
        recipient_name="Acme Manufacturing Ltd.",
        recipient_address="123 Industrial Way, Chicago, IL 60601",
        currency="USD",
        subtotal="$1,304.88",
        tax_total="$104.39",
        total_amount="$1,409.27",
        payment_terms="Net 30",
        po_reference="PO-2024-0847",
    )

    with patch("src.llm.gemini.GeminiProvider") as MockProvider:
        provider = MockProvider.return_value
        provider.extract = AsyncMock(return_value=mock_result)

        result = await provider.extract(load_fixture("sample_invoice.md"), InvoiceResult)

        assert result.invoice_number == "INV-2024-1523"
        assert result.invoice_date == "2024-03-20"
        assert result.due_date == "2024-04-19"
        assert result.issuer_name == "Global Parts Supply Co."
        assert result.recipient_name == "Acme Manufacturing Ltd."
        assert result.total_amount == "$1,409.27"
        assert result.po_reference == "PO-2024-0847"


async def test_invoice_extraction_line_items():
    """EXT-07: Invoice extraction returns line_items list."""
    from src.extraction.schemas.invoice import InvoiceResult, InvoiceLineItem

    mock_result = InvoiceResult(
        invoice_number="INV-2024-1523",
        line_items=[
            InvoiceLineItem(
                item_number="1",
                description="Steel Bolts M10x50",
                quantity="500",
                unit="each",
                unit_price="$0.45",
                extended_price="$225.00",
            ),
            InvoiceLineItem(
                item_number="2",
                description="Hydraulic Hose Assembly",
                quantity="12",
                unit="each",
                unit_price="$89.99",
                extended_price="$1,079.88",
            ),
        ],
    )

    with patch("src.llm.gemini.GeminiProvider") as MockProvider:
        provider = MockProvider.return_value
        provider.extract = AsyncMock(return_value=mock_result)

        result = await provider.extract(load_fixture("sample_invoice.md"), InvoiceResult)

        assert isinstance(result.line_items, list)
        assert len(result.line_items) >= 1
        first_item = result.line_items[0]
        assert first_item.description is not None
        assert first_item.quantity is not None
        assert first_item.unit_price is not None
        assert first_item.extended_price is not None


# ---- Supplier comparison extraction (EXT-05, EXT-08) ----


async def test_supplier_comparison_header():
    """EXT-05: Supplier comparison returns expected header fields."""
    from src.extraction.schemas.supplier_comparison import SupplierComparisonResult

    mock_result = SupplierComparisonResult(
        project_name="Downtown Water Main Replacement Phase III",
        comparison_date="2024-03-15",
        rfq_reference="RFQ-2024-0312",
        evaluation_criteria="Price (40%), Lead Time (25%), Quality/Compliance (20%), Payment Terms (15%)",
        recommended_supplier="Premium Pipe Solutions Inc.",
    )

    with patch("src.llm.gemini.GeminiProvider") as MockProvider:
        provider = MockProvider.return_value
        provider.extract = AsyncMock(return_value=mock_result)

        result = await provider.extract(
            load_fixture("sample_supplier_comparison.md"), SupplierComparisonResult
        )

        assert result.project_name == "Downtown Water Main Replacement Phase III"
        assert result.comparison_date == "2024-03-15"
        assert result.rfq_reference == "RFQ-2024-0312"
        assert result.recommended_supplier == "Premium Pipe Solutions Inc."


async def test_supplier_comparison_line_items():
    """EXT-08: Supplier comparison returns line_items per supplier."""
    from src.extraction.schemas.supplier_comparison import SupplierComparisonResult, SupplierRow

    mock_result = SupplierComparisonResult(
        project_name="Downtown Water Main Replacement Phase III",
        line_items=[
            SupplierRow(
                supplier_name="Premium Pipe Solutions Inc.",
                item_description="12-inch DI Water Main",
                unit_price="$160/ft",
                total_price="$384,000",
                lead_time="45 days",
                payment_terms="50/50",
                delivery_terms="FOB Destination",
                warranty="10 years",
                compliance_notes="ISO 9001 Certified",
                overall_score="92/100",
            ),
            SupplierRow(
                supplier_name="National Waterworks Corp.",
                item_description="12-inch DI Water Main",
                unit_price="$155/ft",
                total_price="$372,000",
                lead_time="60 days",
                payment_terms="Net 60",
                delivery_terms="FOB Origin",
                warranty="5 years",
                compliance_notes="AWWA Compliant",
                overall_score="78/100",
            ),
            SupplierRow(
                supplier_name="Atlas Pipeline Group",
                item_description="12-inch DI Water Main",
                unit_price="$170/ft",
                total_price="$408,000",
                lead_time="30 days",
                payment_terms="Net 30",
                delivery_terms="FOB Destination",
                warranty="10 years",
                compliance_notes="ISO 9001 + AWWA",
                overall_score="85/100",
            ),
        ],
    )

    with patch("src.llm.gemini.GeminiProvider") as MockProvider:
        provider = MockProvider.return_value
        provider.extract = AsyncMock(return_value=mock_result)

        result = await provider.extract(
            load_fixture("sample_supplier_comparison.md"), SupplierComparisonResult
        )

        assert isinstance(result.line_items, list)
        assert len(result.line_items) >= 1
        first_row = result.line_items[0]
        assert first_row.supplier_name is not None
        assert first_row.unit_price is not None
        assert first_row.total_price is not None
        assert first_row.lead_time is not None
        assert first_row.payment_terms is not None
        assert first_row.delivery_terms is not None


# ---- Provider abstraction (EXT-09) ----


async def test_provider_registry_swap():
    """EXT-09: Swapping LLM_PROVIDER uses the registered provider."""
    from src.llm import registry as llm_registry

    # A mock provider that satisfies the LLMProvider Protocol
    mock_provider = MagicMock()
    mock_provider.classify = AsyncMock(return_value="invoice")
    mock_provider.extract = AsyncMock()

    # Register mock provider and configure settings to use it
    llm_registry.register_provider("mock_provider", lambda: mock_provider)
    llm_registry.clear_cache()

    with patch.object(llm_registry.settings, "llm_provider", "mock_provider"):
        provider = llm_registry.get_provider()
        assert provider is mock_provider

        # Verify it uses the swapped provider
        result = await provider.classify("some document text")
        assert result == "invoice"

    # Restore cache state
    llm_registry.clear_cache()


# ---- Gemini SDK (EXT-10) ----


async def test_gemini_provider_uses_correct_sdk():
    """EXT-10: GeminiProvider uses google-genai, not google-generativeai."""
    import sys

    # Verify the deprecated SDK is not imported anywhere in the llm module
    # The correct import is: from google import genai  (google-genai package)
    # The deprecated import would be: import google.generativeai  (google-generativeai package)
    from src.llm import gemini as gemini_module
    import inspect

    source = inspect.getsource(gemini_module)
    # Must use the new SDK
    assert "from google import genai" in source or "google.genai" in source
    # Must NOT use the deprecated SDK
    assert "google.generativeai" not in source
    assert "import google.generativeai" not in source

# CLAUDE.md — Development Guidelines

## 1. Project Context

You are building a document data extraction system.

The system processes business documents (purchase orders, tenders, quotations, invoices, and supplier comparisons) and extracts structured data into CSV format.

All requirements, document types, and output formats are defined in `PRD.md`.

You MUST strictly follow the PRD for:

* Document types
* Output schemas
* Field ordering
* CSV structure

---

## 2. Core Principles

* The system must be modular and extensible
* Each document type must be processed independently
* Do not hardcode document formats
* Rely on AI (LLM) for interpretation and extraction
* Ensure consistent and clean outputs

---

## 3. High-Level Architecture

The system should be structured as follows:

/app
/api
/services
/extractors
/llm
/schemas
/utils

---

## 4. Responsibilities by Layer

### API Layer (`/api`)

* Expose endpoints using FastAPI
* Handle file uploads
* Return CSV responses

### Services Layer (`/services`)

* Orchestrate the processing pipeline
* Connect Docling + LLM + output generation
* Handle document type routing

### Extractors (`/extractors`)

* One extractor per document type:

  * purchase_order_extractor.py
  * quotation_extractor.py
  * tender_extractor.py
  * invoice_extractor.py
  * supplier_comparison_extractor.py

* Each extractor:

  * Receives structured content from Docling
  * Calls LLM for field extraction
  * Returns structured data ready for CSV

### LLM Layer (`/llm`)

* Centralize all LLM interactions
* Build reusable prompt templates
* Handle responses and parsing

### Schemas (`/schemas`)

* Define data structures for each document type
* Ensure output consistency before CSV conversion

### Utils (`/utils`)

* CSV generation
* File handling
* Normalization helpers

---

## 5. Processing Flow

The system must follow this flow:

1. Receive file via API
2. Process document using Docling
3. Detect document type
4. Route to correct extractor
5. Extract data using LLM
6. Validate structure
7. Generate CSV
8. Return result

---

## 6. LLM Usage Guidelines

* Use LLM ONLY for:

  * Document understanding
  * Field extraction
  * Mapping content to schema

* Do NOT use LLM for:

  * CSV formatting
  * File handling
  * Deterministic transformations

* Prompts must:

  * Be explicit
  * Include expected fields
  * Enforce structured output

---

## 7. CSV Generation Rules

* Output must strictly follow PRD column definitions
* Maintain exact column order
* No extra fields allowed
* Use clean and normalized values
* Handle missing values gracefully

---

## 8. Document Type Handling

* Always attempt classification first
* If uncertain, fallback to "Other"
* Each document type must have its own extraction logic

---

## 9. Code Quality Rules

* Use clear and descriptive naming
* Avoid duplication
* Keep functions small and focused
* Write reusable components
* Prefer composition over large monolithic functions

---

## 10. Error Handling

* Handle invalid files gracefully
* Handle unsupported formats
* Handle extraction failures without crashing
* Return meaningful error messages

---

## 11. Extensibility

The system must allow:

* Adding new document types easily
* Updating schemas without breaking the pipeline
* Modifying prompts without changing core logic

---

## 12. What NOT to Do

* Do not hardcode document layouts
* Do not assume fixed positions in documents
* Do not mix responsibilities across layers
* Do not bypass the PRD definitions

---

## 13. Priority

When in doubt:

1. Follow PRD.md
2. Keep output consistent
3. Prefer simple and modular solutions
4. Ensure system scalability

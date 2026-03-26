# PRD — Document Data Extraction System

## 1. Overview

This project is a document data extraction system designed for business and procurement processes.

It processes the following document types:

* Purchase Orders (Ordenes de compra)
* Tenders (Licitaciones)
* Quotations (Cotizaciones)
* Invoices (Facturas)
* Supplier comparison documents included in tender processes

Supported input formats:

* PDF
* Excel (.xlsx)
* Images (PNG, JPG)
* HTML

The system extracts structured data from these documents and outputs a CSV file with a predefined structure depending on the document type.

---

## 2. Objective

The goal of the system is to extract key data from business documents and return it in a structured format, following a predefined field order for each document type.

The system must:

* Identify relevant information from each document
* Structure the data according to the required schema
* Ensure consistency in field ordering
* Output the result as a CSV file

---

## 3. Supported Inputs

The system must accept the following file types:

* PDF (text-based and scanned)
* Excel files (.xlsx)
* Images (PNG, JPG)
* HTML documents

Documents may contain:

* Tables
* Unstructured text
* Mixed layouts
* Multiple sections

---

## 4. Processing Pipeline

The system follows this pipeline:

1. File ingestion
2. Document processing using Docling:

   * Extract structured content from input files
   * Normalize document structure
3. Content interpretation:

   * Identify document type
   * Detect relevant sections (tables, fields, etc.)
4. Data extraction (using AI):

   * Use an LLM to interpret document content
   * Extract key fields based on document type
   * Map extracted data to predefined schema
5. Output generation:

   * Convert structured data into CSV format
   * Ensure correct column order

---

## 5. Document Types

The system must classify and process the following document types:

* Purchase Order
* Tender
* Quotation
* Invoice
* Supplier comparison (within tender context)
* Other (fallback category)

---

## 6. Output Specification

The system must generate a CSV file.

Each document type has its own schema and column structure.

### General Requirements

* Each row represents an item or record
* Column order must be strictly respected
* All values must be normalized
* Missing values should be handled gracefully (empty or null)

---

### Purchase Order (OC)

Columns:

* numero_oc
* cliente
* numero_renglon
* descripcion
* precio_unitario
* subtotal

Additional requirement:

* After listing all items, include one final row with:

  * descripcion: "TOTAL"
  * subtotal: total amount in numeric format

---

### Quotation / Tender

Columns:

* item
* cantidad
* descripcion
* origen

---

### Supplier Comparison

Columns:

* item
* proveedor
* marca
* precio_unitario

---

## 7. Notes

* The system must adapt to different document formats and layouts
* Field detection should be flexible but consistent in output
* Data extraction relies on AI interpretation, not fixed rules
* The CSV output must be clean and ready for downstream processing

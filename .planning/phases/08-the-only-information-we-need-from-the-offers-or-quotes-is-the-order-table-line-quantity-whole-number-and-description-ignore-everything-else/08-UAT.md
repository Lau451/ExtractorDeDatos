---
status: complete
phase: 08-offers-quotes-line-items-only
source: [08-01-SUMMARY.md, 08-02-SUMMARY.md]
started: 2026-03-26T00:00:00Z
updated: 2026-03-26T00:00:00Z
---

## Current Test
<!-- OVERWRITE each test - shows where we are -->

[testing complete]

## Tests

### 1. Tender CSV has exactly 3 columns
expected: Upload or process a tender/RFQ document. The resulting CSV should contain exactly 3 columns: item_number, quantity, description — in that order. No other columns (tender_reference, issue_date, vendor_name, currency, etc.) should appear.
result: pass

### 2. Quotation CSV has exactly 3 columns
expected: Upload or process a quotation document. The resulting CSV should contain exactly 3 columns: item_number, quantity, description — in that order. No other columns (quote_number, vendor_name, grand_total, payment_terms, etc.) should appear.
result: pass

### 3. Quantity normalization — unit suffix stripped
expected: A line item whose quantity value includes a unit suffix (e.g., "5 units", "10 pcs", "3 kg") should appear in the CSV with the numeric part only (e.g., "5", "10", "3"). No trailing unit text in the quantity column.
result: issue
reported: "It works, but it doesn't distinguish between the thousands separator and the decimal point."
severity: major

### 4. Quantity normalization — trailing .0 removed
expected: A line item whose quantity is a whole number expressed as a float (e.g., "2.0", "10.0") should appear in the CSV as a plain integer string ("2", "10"). No ".0" suffix.
result: issue
reported: "It does not distinguish when there are thousands of decimal points."
severity: major

### 5. ReviewTable hidden for tender_rfq
expected: Process a tender/RFQ document through the web UI. After results load, the "header fields" review table (the section showing document-level fields like reference numbers, dates, organizations) should NOT be visible on screen. Only the line items table should show.
result: pass

### 6. ReviewTable hidden for quotation
expected: Process a quotation document through the web UI. After results load, the header fields review table should NOT be visible. Only the line items table should show.
result: pass

### 7. ReviewTable visible for other document types
expected: Process a purchase order, invoice, or supplier comparison through the web UI. The header fields review table SHOULD appear as normal — it is only suppressed for tender and quotation types.
result: pass

## Summary

total: 7
passed: 5
issues: 2
pending: 0
skipped: 0

## Gaps

- truth: "Quantity with unit suffix should be stripped to numeric part only, correctly handling both thousands separators and decimal points"
  status: failed
  reason: "User reported: It works, but it doesn't distinguish between the thousands separator and the decimal point."
  severity: major
  test: 3
  artifacts: []
  missing: []
- truth: "Trailing .0 removal should correctly identify whole-number floats vs. numbers using period as thousands separator"
  status: failed
  reason: "User reported: It does not distinguish when there are thousands of decimal points."
  severity: major
  test: 4
  artifacts: []
  missing: []

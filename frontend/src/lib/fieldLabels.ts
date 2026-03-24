export const FIELD_LABELS: Record<string, string> = {
  // Purchase Order header
  po_number: 'PO Number',
  issue_date: 'Issue Date',
  buyer_name: 'Buyer',
  supplier_name: 'Supplier',
  delivery_date: 'Delivery Date',
  currency: 'Currency',
  total_amount: 'Total Amount',
  payment_terms: 'Payment Terms',
  shipping_address: 'Shipping Address',
  notes: 'Notes',

  // Invoice header
  invoice_number: 'Invoice Number',
  invoice_date: 'Invoice Date',
  due_date: 'Due Date',
  issuer_name: 'Issuer',
  issuer_address: 'Issuer Address',
  recipient_name: 'Recipient',
  recipient_address: 'Recipient Address',
  subtotal: 'Subtotal',
  tax_total: 'Tax Total',
  po_reference: 'PO Reference',

  // Tender/RFQ
  tender_reference: 'Tender Reference',
  issuing_organization: 'Issuing Organization',
  submission_deadline: 'Submission Deadline',
  contact_person: 'Contact Person',
  project_title: 'Project Title',

  // Quotation
  quote_number: 'Quote Number',
  quote_date: 'Quote Date',
  vendor_name: 'Vendor',
  vendor_address: 'Vendor Address',
  valid_until: 'Valid Until',
  grand_total: 'Grand Total',
  delivery_terms: 'Delivery Terms',

  // Supplier Comparison header
  project_name: 'Project Name',
  comparison_date: 'Comparison Date',
  rfq_reference: 'RFQ Reference',
  evaluation_criteria: 'Evaluation Criteria',
  recommended_supplier: 'Recommended Supplier',

  // Line item fields (shared across doc types)
  item_number: 'Item #',
  description: 'Description',
  sku: 'SKU',
  quantity: 'Quantity',
  unit: 'Unit',
  unit_price: 'Unit Price',
  extended_price: 'Extended Price',
  item_description: 'Item Description',
  total_price: 'Total Price',
  lead_time: 'Lead Time',
  warranty: 'Warranty',
  compliance_notes: 'Compliance Notes',
  overall_score: 'Overall Score',
};

/** Fallback: convert snake_case to Title Case */
export function getFieldLabel(key: string): string {
  return FIELD_LABELS[key] ?? key.replace(/_/g, ' ').replace(/\b\w/g, (c) => c.toUpperCase());
}

/** The key within extraction_result that holds the line items array, per doc type */
export const LINE_ITEM_KEYS: Record<string, string> = {
  purchase_order: 'line_items',
  invoice: 'line_items',
  supplier_comparison: 'line_items',
  tender_rfq: 'line_items',
  quotation: 'line_items',
};

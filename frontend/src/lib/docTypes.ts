export const DOC_TYPES_WITH_LINE_ITEMS = new Set([
  'purchase_order',
  'invoice',
  'supplier_comparison',
  'tender_rfq',
  'quotation',
]);

export const VALID_DOC_TYPES = [
  'purchase_order',
  'tender_rfq',
  'quotation',
  'invoice',
  'supplier_comparison',
] as const;

export type DocType = typeof VALID_DOC_TYPES[number];

export const DOC_TYPE_LABELS: Record<string, string> = {
  purchase_order: 'Purchase Order',
  tender_rfq: 'Tender / RFQ',
  quotation: 'Quotation',
  invoice: 'Invoice',
  supplier_comparison: 'Supplier Comparison',
};

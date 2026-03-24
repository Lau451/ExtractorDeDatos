import { describe, it, expect } from 'vitest';
import { LINE_ITEM_KEYS } from '../lib/fieldLabels';
import { DOC_TYPES_WITH_LINE_ITEMS } from '../lib/docTypes';

describe('LineItemsTable constants for tender_rfq and quotation', () => {
  it('LINE_ITEM_KEYS includes tender_rfq mapped to line_items (P6-FE-01)', () => {
    expect(LINE_ITEM_KEYS['tender_rfq']).toBe('line_items');
  });

  it('DOC_TYPES_WITH_LINE_ITEMS includes tender_rfq (P6-FE-01)', () => {
    expect(DOC_TYPES_WITH_LINE_ITEMS.has('tender_rfq')).toBe(true);
  });

  it('LINE_ITEM_KEYS includes quotation mapped to line_items (P6-FE-02)', () => {
    expect(LINE_ITEM_KEYS['quotation']).toBe('line_items');
  });

  it('DOC_TYPES_WITH_LINE_ITEMS includes quotation (P6-FE-02)', () => {
    expect(DOC_TYPES_WITH_LINE_ITEMS.has('quotation')).toBe(true);
  });
});

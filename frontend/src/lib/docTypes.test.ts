import { describe, it, expect } from 'vitest';
import fs from 'node:fs';
import path from 'node:path';
import { LINE_ITEMS_ONLY_DOC_TYPES, VALID_DOC_TYPES } from './docTypes';

describe('LINE_ITEMS_ONLY_DOC_TYPES', () => {
  it('includes tender_rfq', () => {
    expect(LINE_ITEMS_ONLY_DOC_TYPES.has('tender_rfq')).toBe(true);
  });

  it('includes quotation', () => {
    expect(LINE_ITEMS_ONLY_DOC_TYPES.has('quotation')).toBe(true);
  });

  it('excludes purchase_order', () => {
    expect(LINE_ITEMS_ONLY_DOC_TYPES.has('purchase_order')).toBe(false);
  });

  it('excludes invoice', () => {
    expect(LINE_ITEMS_ONLY_DOC_TYPES.has('invoice')).toBe(false);
  });

  it('excludes supplier_comparison', () => {
    expect(LINE_ITEMS_ONLY_DOC_TYPES.has('supplier_comparison')).toBe(false);
  });

  it('contains only valid doc types', () => {
    const validSet = new Set<string>(VALID_DOC_TYPES);
    for (const dt of LINE_ITEMS_ONLY_DOC_TYPES) {
      expect(validSet.has(dt)).toBe(true);
    }
  });

  it('has exactly 2 members', () => {
    expect(LINE_ITEMS_ONLY_DOC_TYPES.size).toBe(2);
  });
});

describe('App.tsx ReviewTable guard (structural)', () => {
  const appSource = fs.readFileSync(
    path.resolve(__dirname, '../App.tsx'),
    'utf-8',
  );

  it('contains the negated LINE_ITEMS_ONLY_DOC_TYPES guard before ReviewTable', () => {
    // The guard pattern: !LINE_ITEMS_ONLY_DOC_TYPES.has(... followed by <ReviewTable
    expect(appSource).toMatch(/!LINE_ITEMS_ONLY_DOC_TYPES\.has\(/);
  });

  it('does not render ReviewTable without the guard', () => {
    // Every <ReviewTable occurrence should be preceded by the guard.
    // Split on <ReviewTable and check each preceding chunk contains the guard.
    const chunks = appSource.split('<ReviewTable');
    // First chunk is before any ReviewTable — skip it.
    // Every subsequent chunk's preceding text (in previous chunk) should contain the guard.
    for (let i = 1; i < chunks.length; i++) {
      const preceding = chunks.slice(0, i).join('<ReviewTable');
      // Find the nearest conditional block before this ReviewTable
      const lastGuardIndex = preceding.lastIndexOf('!LINE_ITEMS_ONLY_DOC_TYPES.has(');
      expect(lastGuardIndex).toBeGreaterThan(-1);
    }
  });

  it('does NOT guard DocTypeBar with LINE_ITEMS_ONLY_DOC_TYPES', () => {
    // DocTypeBar should render for all doc types — no guard
    const docTypeBarSection = appSource.split('<DocTypeBar')[0].slice(-200);
    expect(docTypeBarSection).not.toMatch(/LINE_ITEMS_ONLY_DOC_TYPES/);
  });
});

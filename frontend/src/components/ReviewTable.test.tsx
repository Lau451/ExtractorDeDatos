import { render, screen } from '@testing-library/react';
import { describe, it, expect } from 'vitest';
import { ReviewTable } from './ReviewTable';

const mockData: Record<string, unknown> = {
  invoice_number: 'INV-001',
  invoice_date: '2026-01-15',
  issuer_name: 'Not found',
  total_amount: '$1,000.00',
  line_items: [{ description: 'Widget', quantity: '10' }],
};

describe('ReviewTable', () => {
  it('renders all header fields excluding line_items', () => {
    render(<ReviewTable data={mockData} lineItemKey="line_items" onFieldSave={() => {}} />);
    expect(screen.getByText('INV-001')).toBeInTheDocument();
    expect(screen.getByText('2026-01-15')).toBeInTheDocument();
    expect(screen.getByText('$1,000.00')).toBeInTheDocument();
    // Should NOT render the line_items key as a row
    expect(screen.queryByText('Line Items')).not.toBeInTheDocument(); // 'line_items' label
  });

  it('renders human-readable labels, not snake_case keys', () => {
    render(<ReviewTable data={mockData} lineItemKey="line_items" onFieldSave={() => {}} />);
    expect(screen.getByText('Invoice Number')).toBeInTheDocument();
    expect(screen.getByText('Invoice Date')).toBeInTheDocument();
    expect(screen.getByText('Total Amount')).toBeInTheDocument();
  });

  it('renders Not found values with italic class', () => {
    const { container } = render(<ReviewTable data={mockData} lineItemKey="line_items" onFieldSave={() => {}} />);
    const notFoundSpan = container.querySelector('.italic');
    expect(notFoundSpan).toBeInTheDocument();
    expect(notFoundSpan?.textContent).toBe('Not found');
  });

  it('does not render line_items key as a header field', () => {
    render(<ReviewTable data={mockData} lineItemKey="line_items" onFieldSave={() => {}} />);
    // The table should have 4 rows (invoice_number, invoice_date, issuer_name, total_amount)
    const rows = screen.getAllByRole('row');
    // 1 header row + 4 data rows = 5
    expect(rows.length).toBe(5);
  });
});

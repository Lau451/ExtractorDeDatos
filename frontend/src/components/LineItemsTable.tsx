import {
  Table,
  TableHeader,
  TableBody,
  TableRow,
  TableHead,
  TableCell,
} from '@/components/ui/table';
import { getFieldLabel } from '@/lib/fieldLabels';
import { EditableCell } from './EditableCell';

interface LineItemsTableProps {
  items: Record<string, unknown>[];
  lineItemKey: string;
  onLineItemsSave: (updatedItems: Record<string, unknown>[]) => void;
}

export function LineItemsTable({ items, lineItemKey: _lineItemKey, onLineItemsSave }: LineItemsTableProps) {
  if (items.length === 0) {
    return (
      <div>
        <p className="font-mono text-[20px] font-semibold mb-4 mt-6">Line Items</p>
        <p className="text-muted-foreground italic text-sm">No line items</p>
      </div>
    );
  }

  const columnKeys = Object.keys(items[0] ?? {});

  const handleCellSave = (rowIndex: number, key: string, value: string) => {
    const updatedItems = items.map((item, i) => {
      if (i === rowIndex) {
        return { ...item, [key]: value };
      }
      return { ...item };
    });
    onLineItemsSave(updatedItems);
  };

  return (
    <div>
      <p className="font-mono text-[20px] font-semibold mb-4 mt-6">Line Items</p>
      <Table className="w-full">
        <TableHeader>
          <TableRow>
            {columnKeys.map((key) => (
              <TableHead key={key} className="font-mono text-xs">
                {getFieldLabel(key)}
              </TableHead>
            ))}
          </TableRow>
        </TableHeader>
        <TableBody>
          {items.map((item, rowIndex) => (
            <TableRow key={rowIndex}>
              {columnKeys.map((key) => (
                <TableCell key={key}>
                  <EditableCell
                    value={String(item[key] ?? 'Not found')}
                    onSave={(v) => handleCellSave(rowIndex, key, v)}
                  />
                </TableCell>
              ))}
            </TableRow>
          ))}
        </TableBody>
      </Table>
    </div>
  );
}

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

interface ReviewTableProps {
  data: Record<string, unknown>;
  lineItemKey: string | null;
  onFieldSave: (field: string, value: string) => void;
}

export function ReviewTable({ data, lineItemKey, onFieldSave }: ReviewTableProps) {
  const entries = Object.entries(data).filter(([key]) => key !== lineItemKey);

  return (
    <div>
      <p className="font-mono text-[20px] font-semibold mb-4">Extracted Fields</p>
      <Table className="w-full">
        <TableHeader>
          <TableRow>
            <TableHead className="w-[35%] font-mono text-xs">Field</TableHead>
            <TableHead className="w-[65%] font-mono text-xs">Value</TableHead>
          </TableRow>
        </TableHeader>
        <TableBody>
          {entries.map(([key, val]) => (
            <TableRow key={key}>
              <TableCell className="font-mono text-xs">{getFieldLabel(key)}</TableCell>
              <TableCell>
                <EditableCell
                  value={String(val ?? 'Not found')}
                  onSave={(v) => onFieldSave(key, v)}
                />
              </TableCell>
            </TableRow>
          ))}
        </TableBody>
      </Table>
    </div>
  );
}

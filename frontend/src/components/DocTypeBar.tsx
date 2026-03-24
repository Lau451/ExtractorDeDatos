import { Badge } from '@/components/ui/badge';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import { DOC_TYPE_LABELS, VALID_DOC_TYPES } from '@/lib/docTypes';

interface DocTypeBarProps {
  docType: string;
  onOverride: (newType: string) => void;
}

export function DocTypeBar({ docType, onOverride }: DocTypeBarProps) {
  return (
    <div className="flex flex-row gap-3 items-center mb-4">
      <span className="font-mono text-xs text-muted-foreground">Document type</span>
      <Badge variant="secondary">{DOC_TYPE_LABELS[docType] ?? docType}</Badge>
      <Select onValueChange={(value) => { if (value) onOverride(value as string); }}>
        <SelectTrigger className="w-[200px]">
          <SelectValue placeholder="Override type" />
        </SelectTrigger>
        <SelectContent>
          {VALID_DOC_TYPES.map((type) => (
            <SelectItem key={type} value={type}>
              {DOC_TYPE_LABELS[type]}
            </SelectItem>
          ))}
        </SelectContent>
      </Select>
    </div>
  );
}

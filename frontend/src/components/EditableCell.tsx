import { useState, useEffect } from 'react';
import { cn } from '@/lib/utils';

interface EditableCellProps {
  value: string;
  onSave: (v: string) => void;
}

export function EditableCell({ value, onSave }: EditableCellProps) {
  const [editing, setEditing] = useState(false);
  const [draft, setDraft] = useState(value);

  // Sync draft when value prop changes from parent
  useEffect(() => {
    if (!editing) {
      setDraft(value);
    }
  }, [value, editing]);

  const commit = () => {
    setEditing(false);
    const changed = draft !== value;
    const emptyFromNotFound = draft === '' && value === 'Not found';
    if (changed && !emptyFromNotFound) {
      onSave(draft);
    } else {
      // Reset draft to original value if not saving
      setDraft(value);
    }
  };

  if (editing) {
    return (
      <input
        autoFocus
        value={draft}
        onChange={(e) => setDraft(e.target.value)}
        onBlur={commit}
        onKeyDown={(e) => {
          if (e.key === 'Enter') {
            commit();
          } else if (e.key === 'Escape') {
            setEditing(false);
            setDraft(value);
          }
        }}
        className="w-full bg-transparent border-b border-primary outline-none px-1"
      />
    );
  }

  return (
    <span
      onClick={() => {
        setDraft(value === 'Not found' ? '' : value);
        setEditing(true);
      }}
      className={cn(
        'cursor-pointer hover:bg-muted/50 px-1 rounded min-h-[44px] flex items-center',
        value === 'Not found' && 'text-muted-foreground italic'
      )}
    >
      {value}
    </span>
  );
}

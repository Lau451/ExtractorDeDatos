import { Loader2, AlertCircle } from 'lucide-react';
import { getStatusText } from '@/lib/statusText';
import { getErrorMessage } from '@/lib/errorMessages';
import { Button } from '@/components/ui/button';

interface ProgressViewProps {
  status: string;
  errorCode: string | null;
  errorMessage: string | null;
  onRetry: () => void;
}

export function ProgressView({ status, errorCode, onRetry }: ProgressViewProps) {
  if (status === 'error') {
    return (
      <div className="flex flex-col items-center justify-center min-h-[80px] bg-card rounded-lg p-6 text-center gap-4">
        <AlertCircle className="text-destructive h-8 w-8" />
        <div>
          <p className="font-mono text-[20px] font-semibold leading-[1.2]">Processing failed</p>
          <p className="text-sm text-muted-foreground mt-1">{getErrorMessage(errorCode)}</p>
        </div>
        <Button
          variant="outline"
          className="border-destructive text-destructive"
          onClick={onRetry}
        >
          Try again
        </Button>
      </div>
    );
  }

  return (
    <div className="flex flex-col items-center justify-center min-h-[80px] p-8 text-center">
      <Loader2 className="animate-spin h-8 w-8 text-muted-foreground" />
      <p className="font-mono text-[20px] font-semibold leading-[1.2] mt-4">
        {getStatusText(status)}
      </p>
    </div>
  );
}

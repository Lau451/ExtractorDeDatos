import { useEffect, useRef, useState } from 'react';
import { api } from '@/lib/api';
import type { JobResponse } from '@/types/api';

export function useJobPoller(
  jobId: string | null,
  options: {
    onComplete: (data: JobResponse) => void;
    onError: (data: JobResponse) => void;
    pollingKey?: number;
  }
) {
  const [status, setStatus] = useState<string | null>(null);
  const [data, setData] = useState<JobResponse | null>(null);
  const intervalRef = useRef<ReturnType<typeof setInterval> | null>(null);
  const { onComplete, onError, pollingKey = 0 } = options;

  useEffect(() => {
    if (!jobId) return;

    const id = setInterval(async () => {
      try {
        const res = await api.getJob(jobId);
        setStatus(res.status);
        setData(res);
        if (res.status === 'complete') {
          clearInterval(id);
          onComplete(res);
        } else if (res.status === 'error') {
          clearInterval(id);
          onError(res);
        }
      } catch {
        // Network error during poll — keep polling
      }
    }, 1500);

    intervalRef.current = id;

    return () => clearInterval(id);
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [jobId, pollingKey]);

  return { status, data };
}

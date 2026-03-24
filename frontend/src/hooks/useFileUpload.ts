import { useState } from 'react';
import { api } from '@/lib/api';

export function useFileUpload(options: {
  onSuccess: (jobId: string) => void;
  onError: (msg: string) => void;
}) {
  const [uploading, setUploading] = useState(false);

  async function upload(file: File): Promise<void> {
    setUploading(true);
    try {
      const res = await api.postExtract(file);
      options.onSuccess(res.job_id);
    } catch (err) {
      const msg = err instanceof Error ? err.message : 'Upload failed';
      options.onError(msg);
    } finally {
      setUploading(false);
    }
  }

  return { upload, uploading };
}

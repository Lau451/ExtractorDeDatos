import type { ExtractResponse, JobResponse } from '@/types/api';

export const api = {
  async postExtract(file: File): Promise<ExtractResponse> {
    const form = new FormData();
    form.append('file', file);
    const res = await fetch('/api/extract', { method: 'POST', body: form });
    if (!res.ok) {
      const err = await res.json();
      throw new Error(err.message || err.error || 'Upload failed');
    }
    return res.json();
  },

  async getJob(jobId: string): Promise<JobResponse> {
    const res = await fetch(`/api/jobs/${jobId}`);
    return res.json();
  },

  async patchDocType(jobId: string, docType: string): Promise<void> {
    const res = await fetch(`/api/jobs/${jobId}/doc_type`, {
      method: 'PATCH',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ doc_type: docType }),
    });
    if (!res.ok) {
      const err = await res.json();
      throw new Error(err.message || err.error || 'Doc type update failed');
    }
  },

  async patchFields(jobId: string, fields: Record<string, unknown>): Promise<JobResponse> {
    const res = await fetch(`/api/jobs/${jobId}/fields`, {
      method: 'PATCH',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ fields }),
    });
    if (!res.ok) {
      const err = await res.json();
      throw new Error(err.message || err.error || 'Field update failed');
    }
    return res.json();
  },

  exportUrl(jobId: string): string {
    return `/api/jobs/${jobId}/export`;
  },
};

import { useState, useEffect } from 'react';
import type { JobResponse } from '@/types/api';
import { api } from '@/lib/api';
import { UploadZone } from '@/components/UploadZone';
import { ProgressView } from '@/components/ProgressView';
import { ReviewTable } from '@/components/ReviewTable';
import { LineItemsTable } from '@/components/LineItemsTable';
import { DocTypeBar } from '@/components/DocTypeBar';
import { useFileUpload } from '@/hooks/useFileUpload';
import { useJobPoller } from '@/hooks/useJobPoller';
import { Button } from '@/components/ui/button';
import { Download } from 'lucide-react';
import { LINE_ITEM_KEYS } from '@/lib/fieldLabels';
import { DOC_TYPES_WITH_LINE_ITEMS } from '@/lib/docTypes';

type Phase =
  | { tag: 'upload' }
  | { tag: 'processing'; jobId: string }
  | { tag: 'review'; jobId: string; jobData: JobResponse }
  | { tag: 'done'; jobId: string; jobData: JobResponse };

function App() {
  const [phase, setPhase] = useState<Phase>({ tag: 'upload' });
  const [pollingStatus, setPollingStatus] = useState<string | null>(null);
  const [pollingError, setPollingError] = useState<{
    code: string | null;
    message: string | null;
  } | null>(null);
  const [pollingKey, setPollingKey] = useState(0);
  const [jobData, setJobData] = useState<JobResponse | null>(null);

  // Sync jobData when phase changes to review
  useEffect(() => {
    if (phase.tag === 'review') {
      setJobData(phase.jobData);
    }
  }, [phase]);

  const { upload, uploading } = useFileUpload({
    onSuccess: (jobId) => {
      setPollingStatus(null);
      setPollingError(null);
      setPhase({ tag: 'processing', jobId });
    },
    onError: (msg) => {
      setPollingError({ code: null, message: msg });
    },
  });

  const jobId = phase.tag === 'processing' ? phase.jobId : null;

  const { status: polledStatus } = useJobPoller(jobId, {
    pollingKey,
    onComplete: (data) => {
      setPhase({ tag: 'review', jobId: data.job_id, jobData: data });
    },
    onError: (data) => {
      setPollingError({ code: data.error_code, message: data.error_message });
      setPollingStatus('error');
    },
  });

  // Sync polled status into local state for ProgressView display
  if (polledStatus && polledStatus !== pollingStatus && !pollingError) {
    setPollingStatus(polledStatus);
  }

  const handleRetry = () => {
    setPhase({ tag: 'upload' });
    setPollingStatus(null);
    setPollingError(null);
    setPollingKey((k) => k + 1);
  };

  const handleReset = () => {
    setPhase({ tag: 'upload' });
    setPollingStatus(null);
    setPollingError(null);
    setPollingKey((k) => k + 1);
    setJobData(null);
  };

  const handleDocTypeOverride = async (newType: string) => {
    if (phase.tag !== 'review') return;
    const currentJobId = phase.jobId;
    await api.patchDocType(currentJobId, newType);
    // Re-enter processing phase to re-poll after doc type change
    setPollingStatus(null);
    setPollingError(null);
    setPollingKey((k) => k + 1);
    setPhase({ tag: 'processing', jobId: currentJobId });
  };

  const handleFieldSave = async (field: string, value: string) => {
    if (phase.tag !== 'review') return;
    const updated = await api.patchFields(phase.jobId, { [field]: value });
    setJobData(updated);
  };

  const handleLineItemsSave = async (updatedItems: Record<string, unknown>[]) => {
    if (phase.tag !== 'review') return;
    const updated = await api.patchFields(phase.jobId, { line_items: updatedItems });
    setJobData(updated);
  };

  const handleDownloadCSV = (currentJobId: string, currentJobData: JobResponse) => {
    window.open(api.exportUrl(currentJobId), '_blank');
    setPhase({ tag: 'done', jobId: currentJobId, jobData: currentJobData });
  };

  const currentStatus = pollingError ? 'error' : (pollingStatus ?? 'pending');

  return (
    <div className="min-h-screen bg-background font-sans flex items-start justify-center pt-16">
      <div className="w-full max-w-3xl px-6">
        <p className="font-mono text-[20px] font-semibold mb-8">DocExtract</p>

        {phase.tag === 'upload' && (
          <UploadZone
            onFileAccepted={(file) => upload(file)}
            uploading={uploading}
          />
        )}

        {phase.tag === 'processing' && (
          <ProgressView
            status={currentStatus}
            errorCode={pollingError?.code ?? null}
            errorMessage={pollingError?.message ?? null}
            onRetry={handleRetry}
          />
        )}

        {phase.tag === 'review' && jobData && (
          <div>
            <DocTypeBar
              docType={jobData.doc_type ?? 'unknown'}
              onOverride={handleDocTypeOverride}
            />
            <ReviewTable
              data={jobData.extraction_result ?? {}}
              lineItemKey={LINE_ITEM_KEYS[jobData.doc_type ?? ''] ?? null}
              onFieldSave={handleFieldSave}
            />
            {DOC_TYPES_WITH_LINE_ITEMS.has(jobData.doc_type ?? '') &&
              Array.isArray((jobData.extraction_result ?? {})['line_items']) &&
              ((jobData.extraction_result ?? {})['line_items'] as unknown[]).length > 0 && (
                <LineItemsTable
                  items={(jobData.extraction_result!['line_items'] as Record<string, unknown>[])}
                  lineItemKey={LINE_ITEM_KEYS[jobData.doc_type!]}
                  onLineItemsSave={handleLineItemsSave}
                />
              )}
            <div className="mt-6">
              <Button
                variant="default"
                onClick={() => handleDownloadCSV(phase.jobId, jobData)}
              >
                <Download className="mr-2 h-4 w-4" />
                Download CSV
              </Button>
            </div>
          </div>
        )}

        {phase.tag === 'done' && (
          <div className="flex justify-center">
            <Button
              variant="outline"
              className="border-primary text-primary"
              onClick={handleReset}
            >
              Upload another document
            </Button>
          </div>
        )}
      </div>
    </div>
  );
}

export default App;

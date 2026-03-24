import { useState } from 'react';
import type { JobResponse } from '@/types/api';
import { api } from '@/lib/api';
import { UploadZone } from '@/components/UploadZone';
import { ProgressView } from '@/components/ProgressView';
import { useFileUpload } from '@/hooks/useFileUpload';
import { useJobPoller } from '@/hooks/useJobPoller';

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

  const handleDownload = (currentJobId: string, jobData: JobResponse) => {
    window.open(api.exportUrl(currentJobId), '_blank');
    setPhase({ tag: 'done', jobId: currentJobId, jobData });
  };

  const handleReset = () => {
    setPhase({ tag: 'upload' });
    setPollingStatus(null);
    setPollingError(null);
    setPollingKey((k) => k + 1);
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

        {phase.tag === 'review' && (
          <div>
            <p>Review table — Plan 03</p>
            <button onClick={() => handleDownload(phase.jobId, phase.jobData)}>
              Download CSV
            </button>
          </div>
        )}

        {phase.tag === 'done' && (
          <div>
            <p>Done — Plan 03</p>
            <button onClick={handleReset}>Upload another document</button>
          </div>
        )}
      </div>
    </div>
  );
}

export default App;

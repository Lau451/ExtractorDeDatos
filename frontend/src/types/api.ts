export interface ExtractResponse {
  job_id: string;
  status: string;
}

export interface JobResponse {
  job_id: string;
  status: 'pending' | 'processing' | 'classifying' | 'extracting' | 'complete' | 'error' | string;
  result: { raw_text: string } | null;
  doc_type: string | null;
  extraction_result: Record<string, unknown> | null;
  error_code: string | null;
  error_message: string | null;
}

export interface DocTypeOverrideRequest {
  doc_type: string;
}

export interface PatchFieldsRequest {
  fields: Record<string, unknown>;
}

export interface ErrorResponse {
  error: string;
  message: string;
}

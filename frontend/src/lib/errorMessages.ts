export const ERROR_MESSAGES: Record<string, string> = {
  DOCLING_TIMEOUT: 'The document took too long to parse. Try a smaller file.',
  DOCLING_PARSE_ERROR: 'The document could not be read. Check the file is not corrupted.',
  GEMINI_ERROR: 'Gemini failed to process this document. Try uploading again.',
  INVALID_FILE_TYPE: 'Unsupported file type. Supported: PDF, XLSX, XLS, PNG, JPG, HTML.',
  FILE_TOO_LARGE: 'File is too large to process.',
};

export function getErrorMessage(code: string | null): string {
  if (!code) return 'An unexpected error occurred.';
  return ERROR_MESSAGES[code] ?? `Processing failed (${code}).`;
}

export const STATUS_TEXT: Record<string, string> = {
  pending: 'Uploading...',
  processing: 'Parsing document...',
  classifying: 'Classifying document...',
  extracting: 'Extracting fields...',
};

export function getStatusText(status: string): string {
  return STATUS_TEXT[status] ?? 'Processing...';
}

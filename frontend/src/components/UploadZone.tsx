import { useDropzone } from 'react-dropzone';
import { Upload } from 'lucide-react';

interface UploadZoneProps {
  onFileAccepted: (file: File) => void;
  uploading: boolean;
}

export function UploadZone({ onFileAccepted, uploading }: UploadZoneProps) {
  const { getRootProps, getInputProps, isDragActive, fileRejections } = useDropzone({
    accept: {
      'application/pdf': ['.pdf'],
      'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet': ['.xlsx'],
      'application/vnd.ms-excel': ['.xls'],
      'image/png': ['.png'],
      'image/jpeg': ['.jpg', '.jpeg'],
      'text/html': ['.html'],
    },
    multiple: false,
    disabled: uploading,
    onDrop: (acceptedFiles) => {
      if (acceptedFiles.length === 1) {
        onFileAccepted(acceptedFiles[0]);
      }
    },
  });

  return (
    <div>
      <div
        {...getRootProps()}
        className={[
          'flex flex-col items-center justify-center min-h-[160px] border-2 border-dashed rounded-lg p-8 cursor-pointer transition-colors',
          isDragActive
            ? 'border-primary bg-primary/5'
            : 'border-muted-foreground',
          uploading ? 'opacity-50 cursor-not-allowed' : '',
        ].join(' ')}
      >
        <input {...getInputProps()} />
        <Upload size={48} className="text-muted-foreground mb-4" />
        <p className="font-mono text-[28px] font-semibold leading-[1.1] text-center">
          Drop your document here
        </p>
        <p className="text-sm text-muted-foreground mt-2 text-center">
          or click to browse — PDF, XLSX, XLS, PNG, JPG, HTML
        </p>
      </div>
      {fileRejections.length > 0 && (
        <p className="text-sm text-destructive mt-2">
          Unsupported file type. Please upload a PDF, XLSX, XLS, PNG, JPG, or HTML file.
        </p>
      )}
    </div>
  );
}

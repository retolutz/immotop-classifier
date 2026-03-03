"use client";

import { useCallback } from "react";
import { useDropzone } from "react-dropzone";
import { Upload, FileText, Image, AlertCircle } from "lucide-react";

interface FileDropzoneProps {
  onFileSelect: (file: File) => void;
  isLoading?: boolean;
  error?: string | null;
}

export function FileDropzone({
  onFileSelect,
  isLoading,
  error,
}: FileDropzoneProps) {
  const onDrop = useCallback(
    (acceptedFiles: File[]) => {
      if (acceptedFiles.length > 0) {
        onFileSelect(acceptedFiles[0]);
      }
    },
    [onFileSelect]
  );

  const { getRootProps, getInputProps, isDragActive, acceptedFiles } =
    useDropzone({
      onDrop,
      accept: {
        "application/pdf": [".pdf"],
        "image/png": [".png"],
        "image/jpeg": [".jpg", ".jpeg"],
        "image/tiff": [".tiff"],
        "image/bmp": [".bmp"],
      },
      maxFiles: 1,
      disabled: isLoading,
    });

  const getFileIcon = (filename: string) => {
    if (filename.toLowerCase().endsWith(".pdf")) {
      return <FileText className="w-8 h-8 text-red-500" />;
    }
    return <Image className="w-8 h-8 text-blue-500" />;
  };

  return (
    <div className="space-y-4">
      <div
        {...getRootProps()}
        className={`
          dropzone
          ${isDragActive ? "dropzone-active" : ""}
          ${isLoading ? "opacity-50 cursor-not-allowed" : ""}
          ${error ? "border-red-400 bg-red-50" : ""}
        `}
      >
        <input {...getInputProps()} />

        {isLoading ? (
          <div className="flex flex-col items-center gap-3">
            <div className="animate-spin rounded-full h-10 w-10 border-b-2 border-immotop-primary" />
            <p className="text-gray-600">Verarbeite Rechnung...</p>
            <p className="text-sm text-gray-400">
              OCR-Extraktion und KI-Klassifikation
            </p>
          </div>
        ) : (
          <div className="flex flex-col items-center gap-3">
            <Upload
              className={`w-12 h-12 ${
                isDragActive ? "text-immotop-primary" : "text-gray-400"
              }`}
            />
            <div>
              <p className="text-lg font-medium text-gray-700">
                {isDragActive
                  ? "Datei hier ablegen"
                  : "Rechnung hierher ziehen"}
              </p>
              <p className="text-sm text-gray-500 mt-1">
                oder klicken zum Auswählen
              </p>
            </div>
            <div className="flex gap-2 text-xs text-gray-400">
              <span className="px-2 py-1 bg-gray-100 rounded">PDF</span>
              <span className="px-2 py-1 bg-gray-100 rounded">PNG</span>
              <span className="px-2 py-1 bg-gray-100 rounded">JPG</span>
              <span className="px-2 py-1 bg-gray-100 rounded">TIFF</span>
            </div>
          </div>
        )}
      </div>

      {error && (
        <div className="flex items-center gap-2 text-red-600 bg-red-50 p-3 rounded-md">
          <AlertCircle className="w-5 h-5" />
          <span>{error}</span>
        </div>
      )}

      {acceptedFiles.length > 0 && !isLoading && (
        <div className="flex items-center gap-3 p-3 bg-gray-50 rounded-md">
          {getFileIcon(acceptedFiles[0].name)}
          <div>
            <p className="font-medium text-gray-700">{acceptedFiles[0].name}</p>
            <p className="text-sm text-gray-500">
              {(acceptedFiles[0].size / 1024).toFixed(1)} KB
            </p>
          </div>
        </div>
      )}
    </div>
  );
}

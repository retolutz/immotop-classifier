"use client";

import { useState, useEffect } from "react";
import { api } from "@/lib/api";
import {
  FileText,
  Maximize2,
  Minimize2,
  Download,
  Loader2,
  QrCode,
  AlertCircle,
} from "lucide-react";

interface PdfViewerProps {
  invoiceId: string;
  filename: string;
}

export function PdfViewer({ invoiceId, filename }: PdfViewerProps) {
  const [isExpanded, setIsExpanded] = useState(false);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [hasQr, setHasQr] = useState(false);
  const [previewUrl, setPreviewUrl] = useState<string | null>(null);

  useEffect(() => {
    const loadPreview = async () => {
      setIsLoading(true);
      setError(null);

      try {
        const preview = await api.getInvoicePreview(invoiceId);
        setHasQr(preview.has_qr);

        // Data URL erstellen
        const dataUrl = `data:${preview.mime_type};base64,${preview.data}`;
        setPreviewUrl(dataUrl);
      } catch (err) {
        setError(err instanceof Error ? err.message : "Fehler beim Laden");
      } finally {
        setIsLoading(false);
      }
    };

    loadPreview();
  }, [invoiceId]);

  const handleDownload = () => {
    if (previewUrl) {
      const link = document.createElement("a");
      link.href = previewUrl;
      link.download = filename;
      link.click();
    }
  };

  const isPdf = filename.toLowerCase().endsWith(".pdf");

  return (
    <div className="card">
      {/* Header */}
      <div className="flex items-center justify-between mb-3">
        <div className="flex items-center gap-2">
          <FileText className="w-5 h-5 text-immotop-primary" />
          <span className="font-medium">Dokumentvorschau</span>
          {hasQr && (
            <span className="flex items-center gap-1 text-xs bg-green-100 text-green-700 px-2 py-0.5 rounded-full">
              <QrCode className="w-3 h-3" />
              QR erkannt
            </span>
          )}
        </div>
        <div className="flex items-center gap-2">
          <button
            onClick={handleDownload}
            className="p-1.5 hover:bg-gray-100 rounded-md transition-colors"
            title="Herunterladen"
          >
            <Download className="w-4 h-4 text-gray-600" />
          </button>
          <button
            onClick={() => setIsExpanded(!isExpanded)}
            className="p-1.5 hover:bg-gray-100 rounded-md transition-colors"
            title={isExpanded ? "Verkleinern" : "Vergrössern"}
          >
            {isExpanded ? (
              <Minimize2 className="w-4 h-4 text-gray-600" />
            ) : (
              <Maximize2 className="w-4 h-4 text-gray-600" />
            )}
          </button>
        </div>
      </div>

      {/* Dateiname */}
      <p className="text-sm text-gray-500 mb-3 truncate">{filename}</p>

      {/* Preview Container */}
      <div
        className={`relative bg-gray-100 rounded-lg overflow-hidden transition-all duration-300 ${
          isExpanded ? "h-[600px]" : "h-[300px]"
        }`}
      >
        {isLoading && (
          <div className="absolute inset-0 flex items-center justify-center bg-gray-100">
            <Loader2 className="w-8 h-8 animate-spin text-immotop-primary" />
          </div>
        )}

        {error && (
          <div className="absolute inset-0 flex flex-col items-center justify-center bg-gray-100 text-gray-500">
            <AlertCircle className="w-8 h-8 mb-2" />
            <p className="text-sm">{error}</p>
          </div>
        )}

        {previewUrl && !isLoading && !error && (
          <>
            {isPdf ? (
              <iframe
                src={previewUrl}
                className="w-full h-full border-0"
                title="PDF Vorschau"
              />
            ) : (
              <img
                src={previewUrl}
                alt={filename}
                className="w-full h-full object-contain"
              />
            )}
          </>
        )}
      </div>

      {/* QR-Code Info */}
      {hasQr && (
        <div className="mt-3 p-2 bg-green-50 rounded-md">
          <p className="text-xs text-green-700">
            <strong>Swiss QR-Bill erkannt:</strong> Zahlungsdaten wurden automatisch aus dem QR-Code extrahiert (100% genau).
          </p>
        </div>
      )}
    </div>
  );
}

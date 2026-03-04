"use client";

import { useState, useEffect } from "react";
import { api } from "@/lib/api";
import type { InvoiceUploadResponse, Konto, Kreditor } from "@/types";
import {
  FileDropzone,
  InvoicePreview,
  AccountSelector,
  SubmitForm,
  KontenplanView,
  PdfViewer,
  ScanningAnimation,
} from "@/components";
import { RefreshCw, AlertCircle } from "lucide-react";

export default function Home() {
  // State
  const [konten, setKonten] = useState<Konto[]>([]);
  const [kreditoren, setKreditoren] = useState<Kreditor[]>([]);
  const [uploadResult, setUploadResult] = useState<InvoiceUploadResponse | null>(null);
  const [selectedKonto, setSelectedKonto] = useState<Konto | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [currentFile, setCurrentFile] = useState<File | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [dataLoaded, setDataLoaded] = useState(false);

  // Lade Stammdaten beim Start
  useEffect(() => {
    const loadData = async () => {
      try {
        const [kontenData, kreditorenData] = await Promise.all([
          api.getKonten(),
          api.getKreditoren(),
        ]);
        setKonten(kontenData);
        setKreditoren(kreditorenData);
        setDataLoaded(true);
      } catch (err) {
        console.error("Fehler beim Laden der Stammdaten:", err);
        // Im Mock-Modus trotzdem weitermachen
        setDataLoaded(true);
      }
    };
    loadData();
  }, []);

  // Datei-Upload Handler
  const handleFileSelect = async (file: File) => {
    setCurrentFile(file);
    setIsLoading(true);
    setError(null);
    setUploadResult(null);
    setSelectedKonto(null);

    try {
      const result = await api.uploadInvoice(file);
      setUploadResult(result);

      // Primäres Konto vorauswählen
      const primaryKonto = konten.find(
        (k) => k.s_seqnr === result.classification.primary.konto_seqnr
      );
      if (primaryKonto) {
        setSelectedKonto(primaryKonto);
      }
    } catch (err) {
      setError(
        err instanceof Error ? err.message : "Fehler beim Hochladen der Datei"
      );
    } finally {
      setIsLoading(false);
      setCurrentFile(null);
    }
  };

  // Neue Rechnung starten
  const handleReset = () => {
    setUploadResult(null);
    setSelectedKonto(null);
    setError(null);
  };

  return (
    <div className="space-y-8">
      {/* Scanning Animation */}
      {isLoading && currentFile && (
        <div className="max-w-2xl mx-auto py-8">
          <ScanningAnimation file={currentFile} />
        </div>
      )}

      {/* Error Display */}
      {error && !isLoading && (
        <div className="max-w-2xl mx-auto mb-6">
          <div className="flex items-center gap-2 text-red-600 bg-red-50 p-4 rounded-lg border border-red-200">
            <AlertCircle className="w-5 h-5 flex-shrink-0" />
            <span>{error}</span>
          </div>
        </div>
      )}

      {/* Upload-Bereich */}
      {!uploadResult && !isLoading && (
        <div className="max-w-2xl mx-auto">
          <div className="text-center mb-6">
            <h2 className="text-2xl font-bold text-gray-800">
              Rechnung klassifizieren
            </h2>
            <p className="text-gray-600 mt-2">
              Laden Sie eine Rechnung hoch, um sie automatisch dem richtigen
              Konto zuzuordnen.
            </p>
          </div>
          <FileDropzone
            onFileSelect={handleFileSelect}
            isLoading={isLoading}
            error={error}
          />

          {/* Info-Box */}
          <div className="mt-6 p-4 bg-blue-50 rounded-lg">
            <h3 className="font-medium text-blue-800 mb-2">So funktioniert's:</h3>
            <ol className="list-decimal list-inside text-sm text-blue-700 space-y-1">
              <li>Rechnung als PDF oder Bild hochladen</li>
              <li>KI analysiert den Inhalt und schlägt das passende Konto vor</li>
              <li>Vorschlag prüfen oder alternatives Konto wählen</li>
              <li>Mit einem Klick an Immotop2 senden</li>
            </ol>
          </div>

          {/* Kontenplan */}
          {konten.length > 0 && !isLoading && (
            <div className="mt-6">
              <KontenplanView konten={konten} />
            </div>
          )}
        </div>
      )}

      {/* Ergebnis-Ansicht */}
      {uploadResult && (
        <div>
          {/* Toolbar */}
          <div className="flex items-center justify-between mb-6">
            <h2 className="text-xl font-bold text-gray-800">
              Klassifikationsergebnis
            </h2>
            <button
              onClick={handleReset}
              className="btn btn-secondary flex items-center gap-2"
            >
              <RefreshCw className="w-4 h-4" />
              Neue Rechnung
            </button>
          </div>

          {/* Hauptbereich - 3 Spalten auf grossen Bildschirmen */}
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
            {/* Linke Spalte: PDF-Vorschau */}
            <div className="lg:col-span-1">
              <PdfViewer
                invoiceId={uploadResult.id}
                filename={uploadResult.filename}
              />
            </div>

            {/* Mittlere Spalte: Rechnungsdaten */}
            <div className="lg:col-span-1">
              <InvoicePreview
                data={uploadResult.invoice_data}
                filename={uploadResult.filename}
              />
            </div>

            {/* Rechte Spalte: Kontenzuordnung & Submit */}
            <div className="lg:col-span-1 space-y-6">
              <AccountSelector
                classification={uploadResult.classification}
                konten={konten}
                selectedKonto={selectedKonto}
                onSelect={setSelectedKonto}
              />

              {selectedKonto && (
                <SubmitForm
                  invoiceId={uploadResult.id}
                  invoiceData={uploadResult.invoice_data}
                  classification={uploadResult.classification}
                  selectedKonto={selectedKonto}
                  kreditoren={kreditoren}
                />
              )}
            </div>
          </div>
        </div>
      )}

      {/* Backend-Status */}
      {!dataLoaded && (
        <div className="fixed bottom-4 right-4 flex items-center gap-2 bg-yellow-100 text-yellow-800 px-4 py-2 rounded-lg shadow">
          <AlertCircle className="w-4 h-4" />
          <span className="text-sm">Verbinde mit Backend...</span>
        </div>
      )}
    </div>
  );
}

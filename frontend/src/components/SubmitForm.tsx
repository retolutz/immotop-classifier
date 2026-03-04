"use client";

import { useState, useEffect, useMemo } from "react";
import type {
  InvoiceData,
  ClassificationResult,
  Konto,
  Kreditor,
  ImmotopSubmitRequest,
  ImmotopSubmitResponse,
} from "@/types";
import { api } from "@/lib/api";
import {
  Send,
  Loader2,
  CheckCircle,
  XCircle,
  ExternalLink,
} from "lucide-react";

interface SubmitFormProps {
  invoiceId: string;
  invoiceData: InvoiceData;
  classification: ClassificationResult;
  selectedKonto: Konto;
  kreditoren: Kreditor[];
}

// Hilfsfunktion für Kreditor-Matching
function findMatchingKreditor(
  kreditorName: string | null | undefined,
  kreditoren: Kreditor[]
): Kreditor | null {
  if (!kreditorName || kreditoren.length === 0) return null;

  const searchName = kreditorName.toLowerCase().trim();

  // Exakter Match
  let match = kreditoren.find(
    (k) => k.bez.toLowerCase() === searchName || k.name.toLowerCase() === searchName
  );
  if (match) return match;

  // Partieller Match (Kreditor enthält Suchbegriff oder umgekehrt)
  match = kreditoren.find(
    (k) =>
      k.bez.toLowerCase().includes(searchName) ||
      searchName.includes(k.bez.toLowerCase()) ||
      k.name.toLowerCase().includes(searchName) ||
      searchName.includes(k.name.toLowerCase())
  );
  if (match) return match;

  // Wort-Match (erstes Wort)
  const firstWord = searchName.split(/\s+/)[0];
  if (firstWord.length >= 3) {
    match = kreditoren.find(
      (k) =>
        k.bez.toLowerCase().includes(firstWord) ||
        k.name.toLowerCase().includes(firstWord)
    );
  }

  return match || null;
}

export function SubmitForm({
  invoiceId,
  invoiceData,
  classification,
  selectedKonto,
  kreditoren,
}: SubmitFormProps) {
  const extrahierteDaten = classification.extrahierte_daten || {};

  // Auto-Match Kreditor
  const suggestedKreditor = useMemo(
    () => findMatchingKreditor(extrahierteDaten.kreditor_name, kreditoren),
    [extrahierteDaten.kreditor_name, kreditoren]
  );

  const [selectedKreditor, setSelectedKreditor] = useState<Kreditor | null>(
    suggestedKreditor
  );

  // Buchungstext aus LLM-Extraktion oder Fallback
  const initialBuchungstext = useMemo(() => {
    if (extrahierteDaten.leistungsbeschreibung) {
      return extrahierteDaten.leistungsbeschreibung;
    }
    if (invoiceData.beschreibung) {
      return invoiceData.beschreibung;
    }
    // Fallback: Kreditor + Konto
    const parts = [];
    if (extrahierteDaten.kreditor_name) {
      parts.push(extrahierteDaten.kreditor_name);
    }
    if (selectedKonto?.bez) {
      parts.push(selectedKonto.bez);
    }
    return parts.join(" - ") || "";
  }, [extrahierteDaten, invoiceData.beschreibung, selectedKonto]);

  const [buchungstext, setBuchungstext] = useState(initialBuchungstext);

  // Update wenn sich suggestedKreditor ändert
  useEffect(() => {
    if (suggestedKreditor && !selectedKreditor) {
      setSelectedKreditor(suggestedKreditor);
    }
  }, [suggestedKreditor, selectedKreditor]);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [result, setResult] = useState<ImmotopSubmitResponse | null>(null);

  const handleSubmit = async () => {
    if (!selectedKreditor) {
      alert("Bitte wählen Sie einen Kreditor");
      return;
    }

    setIsSubmitting(true);
    setResult(null);

    try {
      // Datum: OCR -> LLM -> Heute
      const belegdatum =
        invoiceData.rechnungsdatum ||
        extrahierteDaten.rechnungsdatum ||
        new Date().toISOString().split("T")[0];

      // MwSt-Daten berechnen
      const bruttobetrag = invoiceData.bruttobetrag || 0;
      const mwstSatz = invoiceData.mwst_satz || null;
      const mwstBetrag = invoiceData.mwst_betrag || null;
      const nettobetrag = invoiceData.nettobetrag ||
        (mwstBetrag ? bruttobetrag - mwstBetrag : null);

      const request: ImmotopSubmitRequest = {
        invoice_id: invoiceId,
        mandant_seqnr: 1,
        kreditor_seqnr: selectedKreditor.s_seqnr,
        belegdatum,
        faelligkeitsdatum: invoiceData.faelligkeitsdatum,
        bruttobetrag,
        buchungstext: buchungstext || "Rechnung",
        positionen: [
          {
            konto_seqnr: selectedKonto.s_seqnr,
            kostenstelle_seqnr: null,
            bruttobetrag,
            betrag_exkl_mwst: nettobetrag,
            betrag_mwst: mwstBetrag,
            mwst_satz: mwstSatz,
            mwst_code_seqnr: null,
            buchungstext: buchungstext || "Rechnung",
          },
        ],
        // Zusätzliche Felder
        rechnungsnummer: invoiceData.rechnungsnummer,
        esrreferenznummer: invoiceData.qr_referenz,
        qrcodepayload: null, // TODO: QR-Code Payload speichern
        kreditor_iban: invoiceData.iban,
      };

      const response = await api.submitToImmotop(request);
      setResult(response);
    } catch (error) {
      setResult({
        success: false,
        import_seqnr: null,
        beleg_seqnr: null,
        message: error instanceof Error ? error.message : "Unbekannter Fehler",
        immotop_url: null,
      });
    } finally {
      setIsSubmitting(false);
    }
  };

  // Erfolgsmeldung
  if (result?.success) {
    return (
      <div className="card bg-green-50 border-2 border-green-200">
        <div className="flex items-center gap-3 text-green-700">
          <CheckCircle className="w-8 h-8" />
          <div>
            <h3 className="font-semibold text-lg">Erfolgreich gesendet!</h3>
            <p className="text-sm">{result.message}</p>
          </div>
        </div>
        {result.immotop_url && (
          <a
            href={result.immotop_url}
            target="_blank"
            rel="noopener noreferrer"
            className="mt-4 inline-flex items-center gap-2 btn btn-primary"
          >
            <ExternalLink className="w-4 h-4" />
            In Immotop2 öffnen
          </a>
        )}
        {result.beleg_seqnr && (
          <p className="mt-3 text-sm text-green-600">
            Beleg-Nr: {result.beleg_seqnr}
          </p>
        )}
      </div>
    );
  }

  // Fehlermeldung
  if (result && !result.success) {
    return (
      <div className="card bg-red-50 border-2 border-red-200">
        <div className="flex items-center gap-3 text-red-700">
          <XCircle className="w-8 h-8" />
          <div>
            <h3 className="font-semibold text-lg">Fehler beim Senden</h3>
            <p className="text-sm">{result.message}</p>
          </div>
        </div>
        <button
          onClick={() => setResult(null)}
          className="mt-4 btn btn-secondary"
        >
          Erneut versuchen
        </button>
      </div>
    );
  }

  return (
    <div className="card space-y-4">
      <h3 className="font-semibold text-lg">An Immotop2 senden</h3>

      {/* Gewähltes Konto */}
      <div className="p-3 bg-blue-50 rounded-md">
        <p className="text-sm text-gray-500">Gewähltes Konto:</p>
        <p className="font-medium">
          <span className="font-mono">{selectedKonto.kontonr}</span> -{" "}
          {selectedKonto.bez}
        </p>
      </div>

      {/* Kreditor Auswahl */}
      <div>
        <label className="block text-sm font-medium text-gray-700 mb-1">
          Kreditor
          {suggestedKreditor && (
            <span className="ml-2 text-xs text-green-600 font-normal">
              (automatisch erkannt)
            </span>
          )}
        </label>
        {extrahierteDaten.kreditor_name && !suggestedKreditor && (
          <div className="mb-2 p-3 bg-amber-50 border border-amber-200 rounded-md">
            <p className="text-sm text-amber-800">
              <strong>Erkannt:</strong> &quot;{extrahierteDaten.kreditor_name}&quot;
            </p>
            <p className="text-xs text-amber-600 mt-1">
              Kein passender Kreditor im System gefunden.
            </p>
            <button
              type="button"
              onClick={() => {
                const kreditorName = extrahierteDaten.kreditor_name || "";
                alert(
                  `Neuen Kreditor erfassen:\n\nName: ${kreditorName}\n\nBitte in Immotop2 unter Stammdaten > Kreditoren erfassen.`
                );
              }}
              className="mt-2 text-xs px-3 py-1.5 bg-amber-100 hover:bg-amber-200 text-amber-800 rounded-md transition-colors"
            >
              → Neuen Kreditor in Immotop2 erfassen
            </button>
          </div>
        )}
        <select
          value={selectedKreditor?.s_seqnr || ""}
          onChange={(e) => {
            const kreditor = kreditoren.find(
              (k) => k.s_seqnr === parseInt(e.target.value)
            );
            setSelectedKreditor(kreditor || null);
          }}
          className="w-full px-3 py-2 border rounded-md focus:outline-none focus:ring-2 focus:ring-immotop-primary"
        >
          <option value="">Kreditor wählen...</option>
          {kreditoren.map((kreditor) => (
            <option key={kreditor.s_seqnr} value={kreditor.s_seqnr}>
              {kreditor.bez} ({kreditor.ort || "ohne Ort"})
            </option>
          ))}
        </select>
      </div>

      {/* Buchungstext */}
      <div>
        <label className="block text-sm font-medium text-gray-700 mb-1">
          Buchungstext
        </label>
        <input
          type="text"
          value={buchungstext}
          onChange={(e) => setBuchungstext(e.target.value)}
          placeholder="z.B. Heizöllieferung Januar 2024"
          className="w-full px-3 py-2 border rounded-md focus:outline-none focus:ring-2 focus:ring-immotop-primary"
        />
      </div>

      {/* Zusammenfassung */}
      <div className="p-3 bg-gray-50 rounded-md text-sm space-y-1">
        <div className="flex justify-between">
          <span className="text-gray-500">Bruttobetrag:</span>
          <span className="font-semibold">
            CHF{" "}
            {invoiceData.bruttobetrag?.toLocaleString("de-CH", {
              minimumFractionDigits: 2,
            }) || "0.00"}
          </span>
        </div>
        {invoiceData.mwst_satz && invoiceData.mwst_betrag && (
          <div className="flex justify-between text-xs text-gray-500">
            <span>davon MwSt ({invoiceData.mwst_satz}%):</span>
            <span>
              CHF{" "}
              {invoiceData.mwst_betrag.toLocaleString("de-CH", {
                minimumFractionDigits: 2,
              })}
            </span>
          </div>
        )}
        <div className="flex justify-between">
          <span className="text-gray-500">Datum:</span>
          <span>
            {invoiceData.rechnungsdatum || extrahierteDaten.rechnungsdatum || "Heute"}
            {!invoiceData.rechnungsdatum && extrahierteDaten.rechnungsdatum && (
              <span className="ml-1 text-xs text-green-600">(KI)</span>
            )}
          </span>
        </div>
        {invoiceData.rechnungsnummer && (
          <div className="flex justify-between">
            <span className="text-gray-500">Rechnung Nr.:</span>
            <span className="font-mono text-xs">{invoiceData.rechnungsnummer}</span>
          </div>
        )}
        {invoiceData.qr_referenz && (
          <div className="flex justify-between">
            <span className="text-gray-500">QR-Referenz:</span>
            <span className="font-mono text-xs truncate max-w-[150px]" title={invoiceData.qr_referenz}>
              {invoiceData.qr_referenz}
            </span>
          </div>
        )}
      </div>

      {/* Submit Button */}
      <button
        onClick={handleSubmit}
        disabled={isSubmitting || !selectedKreditor}
        className="w-full btn btn-success flex items-center justify-center gap-2 py-3"
      >
        {isSubmitting ? (
          <>
            <Loader2 className="w-5 h-5 animate-spin" />
            Wird gesendet...
          </>
        ) : (
          <>
            <Send className="w-5 h-5" />
            An Immotop2 senden
          </>
        )}
      </button>
    </div>
  );
}

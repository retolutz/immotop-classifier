"use client";

import { useState } from "react";
import type {
  InvoiceData,
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
  selectedKonto: Konto;
  kreditoren: Kreditor[];
}

export function SubmitForm({
  invoiceId,
  invoiceData,
  selectedKonto,
  kreditoren,
}: SubmitFormProps) {
  const [selectedKreditor, setSelectedKreditor] = useState<Kreditor | null>(
    null
  );
  const [buchungstext, setBuchungstext] = useState(
    invoiceData.beschreibung || ""
  );
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
      const request: ImmotopSubmitRequest = {
        invoice_id: invoiceId,
        mandant_seqnr: 1,
        kreditor_seqnr: selectedKreditor.s_seqnr,
        belegdatum:
          invoiceData.rechnungsdatum || new Date().toISOString().split("T")[0],
        faelligkeitsdatum: invoiceData.faelligkeitsdatum,
        bruttobetrag: invoiceData.bruttobetrag || 0,
        buchungstext: buchungstext || "Rechnung",
        positionen: [
          {
            konto_seqnr: selectedKonto.s_seqnr,
            kostenstelle_seqnr: null,
            bruttobetrag: invoiceData.bruttobetrag || 0,
            buchungstext: buchungstext || "Rechnung",
            mwst_code: null,
          },
        ],
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
        </label>
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
      <div className="p-3 bg-gray-50 rounded-md text-sm">
        <div className="flex justify-between">
          <span className="text-gray-500">Betrag:</span>
          <span className="font-semibold">
            CHF{" "}
            {invoiceData.bruttobetrag?.toLocaleString("de-CH", {
              minimumFractionDigits: 2,
            }) || "0.00"}
          </span>
        </div>
        <div className="flex justify-between mt-1">
          <span className="text-gray-500">Datum:</span>
          <span>{invoiceData.rechnungsdatum || "Heute"}</span>
        </div>
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

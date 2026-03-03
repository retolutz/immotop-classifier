"use client";

import { useState } from "react";
import type { ClassificationResult, Konto } from "@/types";
import { ConfidenceIndicator } from "./ConfidenceIndicator";
import { Check, ChevronDown, AlertTriangle, Lightbulb } from "lucide-react";

interface AccountSelectorProps {
  classification: ClassificationResult;
  konten: Konto[];
  selectedKonto: Konto | null;
  onSelect: (konto: Konto) => void;
}

export function AccountSelector({
  classification,
  konten,
  selectedKonto,
  onSelect,
}: AccountSelectorProps) {
  const [showAllKonten, setShowAllKonten] = useState(false);
  const [searchTerm, setSearchTerm] = useState("");

  const { primary, alternativen, extrahierte_daten } = classification;

  // Finde das primäre Konto in der Kontenliste
  const primaryKonto = konten.find((k) => k.s_seqnr === primary.konto_seqnr);

  // Alternative Konten
  const alternativeKonten = alternativen
    .map((alt) => ({
      suggestion: alt,
      konto: konten.find((k) => k.s_seqnr === alt.konto_seqnr),
    }))
    .filter((item) => item.konto);

  // Gefilterte Konten für manuelle Auswahl
  const filteredKonten = konten.filter(
    (k) =>
      k.kontonr.toLowerCase().includes(searchTerm.toLowerCase()) ||
      k.bez.toLowerCase().includes(searchTerm.toLowerCase())
  );

  const isLowConfidence = primary.konfidenz < 0.5;

  return (
    <div className="card space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <h3 className="font-semibold text-lg">Kontenzuordnung</h3>
        {isLowConfidence && (
          <div className="flex items-center gap-1 text-amber-600 text-sm">
            <AlertTriangle className="w-4 h-4" />
            <span>Manuelle Prüfung empfohlen</span>
          </div>
        )}
      </div>

      {/* Primärer Vorschlag */}
      <div
        className={`p-4 rounded-lg border-2 cursor-pointer transition-colors ${
          selectedKonto?.s_seqnr === primary.konto_seqnr
            ? "border-immotop-primary bg-blue-50"
            : "border-gray-200 hover:border-gray-300"
        }`}
        onClick={() => primaryKonto && onSelect(primaryKonto)}
      >
        <div className="flex items-start justify-between">
          <div className="flex-1">
            <div className="flex items-center gap-2">
              <span className="font-mono text-lg font-bold text-immotop-primary">
                {primary.konto_nr}
              </span>
              <span className="font-medium">{primary.konto_bez}</span>
              {selectedKonto?.s_seqnr === primary.konto_seqnr && (
                <Check className="w-5 h-5 text-green-600" />
              )}
            </div>
            <div className="mt-2">
              <ConfidenceIndicator value={primary.konfidenz} />
            </div>
            <div className="mt-3 flex items-start gap-2 text-sm text-gray-600">
              <Lightbulb className="w-4 h-4 mt-0.5 text-amber-500" />
              <p>{primary.begruendung}</p>
            </div>
          </div>
        </div>
      </div>

      {/* Extrahierte Zusatzinformationen */}
      {Object.keys(extrahierte_daten).length > 0 && (
        <div className="p-3 bg-gray-50 rounded-md">
          <p className="text-sm text-gray-500 mb-2">
            Erkannte Informationen:
          </p>
          <div className="flex flex-wrap gap-2">
            {extrahierte_daten.kreditor_name && (
              <span className="px-2 py-1 bg-white rounded text-sm">
                Kreditor: {extrahierte_daten.kreditor_name}
              </span>
            )}
            {extrahierte_daten.leistungsbeschreibung && (
              <span className="px-2 py-1 bg-white rounded text-sm">
                {extrahierte_daten.leistungsbeschreibung}
              </span>
            )}
            {extrahierte_daten.zeitraum && (
              <span className="px-2 py-1 bg-white rounded text-sm">
                Zeitraum: {extrahierte_daten.zeitraum}
              </span>
            )}
          </div>
        </div>
      )}

      {/* Alternative Vorschläge */}
      {alternativeKonten.length > 0 && (
        <div>
          <p className="text-sm text-gray-500 mb-2">Alternative Konten:</p>
          <div className="space-y-2">
            {alternativeKonten.map(({ suggestion, konto }) => (
              <div
                key={konto!.s_seqnr}
                className={`p-3 rounded-md border cursor-pointer transition-colors ${
                  selectedKonto?.s_seqnr === konto!.s_seqnr
                    ? "border-immotop-primary bg-blue-50"
                    : "border-gray-200 hover:border-gray-300"
                }`}
                onClick={() => onSelect(konto!)}
              >
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-2">
                    <span className="font-mono font-medium">
                      {suggestion.konto_nr}
                    </span>
                    <span className="text-sm">{suggestion.konto_bez}</span>
                    {selectedKonto?.s_seqnr === konto!.s_seqnr && (
                      <Check className="w-4 h-4 text-green-600" />
                    )}
                  </div>
                  <span className="text-sm text-gray-500">
                    {Math.round(suggestion.konfidenz * 100)}%
                  </span>
                </div>
                <p className="text-xs text-gray-500 mt-1">
                  {suggestion.begruendung}
                </p>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Manuelle Kontenauswahl */}
      <div>
        <button
          onClick={() => setShowAllKonten(!showAllKonten)}
          className="flex items-center gap-2 text-sm text-gray-500 hover:text-gray-700"
        >
          <ChevronDown
            className={`w-4 h-4 transition-transform ${
              showAllKonten ? "rotate-180" : ""
            }`}
          />
          Anderes Konto wählen
        </button>

        {showAllKonten && (
          <div className="mt-3 space-y-3">
            <input
              type="text"
              placeholder="Konto suchen..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              className="w-full px-3 py-2 border rounded-md focus:outline-none focus:ring-2 focus:ring-immotop-primary"
            />
            <div className="max-h-60 overflow-y-auto space-y-1">
              {filteredKonten.map((konto) => (
                <div
                  key={konto.s_seqnr}
                  className={`p-2 rounded cursor-pointer transition-colors ${
                    selectedKonto?.s_seqnr === konto.s_seqnr
                      ? "bg-immotop-primary text-white"
                      : "hover:bg-gray-100"
                  }`}
                  onClick={() => {
                    onSelect(konto);
                    setShowAllKonten(false);
                  }}
                >
                  <span className="font-mono">{konto.kontonr}</span>
                  <span className="ml-2">{konto.bez}</span>
                </div>
              ))}
            </div>
          </div>
        )}
      </div>
    </div>
  );
}

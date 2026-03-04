"use client";

import { useState } from "react";
import type { Konto } from "@/types";
import { ChevronDown, ChevronUp, BookOpen, Search } from "lucide-react";

interface KontenplanViewProps {
  konten: Konto[];
}

export function KontenplanView({ konten }: KontenplanViewProps) {
  const [isExpanded, setIsExpanded] = useState(false);
  const [searchTerm, setSearchTerm] = useState("");

  // Filtern nach Suchbegriff
  const filteredKonten = konten.filter(
    (k) =>
      k.kontonr.toLowerCase().includes(searchTerm.toLowerCase()) ||
      k.bez.toLowerCase().includes(searchTerm.toLowerCase())
  );

  // Gruppieren nach erster Ziffer (Kontoklasse)
  const groupedKonten = filteredKonten.reduce((acc, konto) => {
    const group = konto.kontonr.charAt(0);
    if (!acc[group]) {
      acc[group] = [];
    }
    acc[group].push(konto);
    return acc;
  }, {} as Record<string, Konto[]>);

  const kontoKlassen: Record<string, string> = {
    "1": "Aktiven",
    "2": "Passiven",
    "3": "Betriebsertrag",
    "4": "Aufwand Liegenschaften",
    "5": "Personalaufwand",
    "6": "Übriger Aufwand",
    "7": "Abschreibungen",
    "8": "Finanzertrag/-aufwand",
    "9": "Abschluss",
  };

  return (
    <div className="card">
      {/* Header - klickbar zum Ein-/Ausklappen */}
      <button
        onClick={() => setIsExpanded(!isExpanded)}
        className="w-full flex items-center justify-between text-left"
      >
        <div className="flex items-center gap-2">
          <BookOpen className="w-5 h-5 text-immotop-primary" />
          <span className="font-semibold">Kontenplan</span>
          <span className="text-sm text-gray-500">({konten.length} Konten)</span>
        </div>
        {isExpanded ? (
          <ChevronUp className="w-5 h-5 text-gray-400" />
        ) : (
          <ChevronDown className="w-5 h-5 text-gray-400" />
        )}
      </button>

      {/* Inhalt */}
      {isExpanded && (
        <div className="mt-4 space-y-4">
          {/* Suchfeld */}
          <div className="relative">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400" />
            <input
              type="text"
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              placeholder="Konto suchen..."
              className="w-full pl-10 pr-4 py-2 border rounded-md focus:outline-none focus:ring-2 focus:ring-immotop-primary"
            />
          </div>

          {/* Konten-Liste gruppiert */}
          <div className="max-h-96 overflow-y-auto space-y-4">
            {Object.entries(groupedKonten)
              .sort(([a], [b]) => a.localeCompare(b))
              .map(([group, groupKonten]) => (
                <div key={group}>
                  <h4 className="text-sm font-medium text-gray-500 mb-2 sticky top-0 bg-white py-1">
                    {group} - {kontoKlassen[group] || "Andere"}
                  </h4>
                  <div className="space-y-1">
                    {groupKonten.map((konto) => (
                      <div
                        key={konto.s_seqnr}
                        className="flex items-center justify-between py-1.5 px-2 hover:bg-gray-50 rounded text-sm"
                      >
                        <div className="flex items-center gap-2">
                          <span className="font-mono text-immotop-primary font-medium">
                            {konto.kontonr}
                          </span>
                          <span className="text-gray-700">{konto.bez}</span>
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              ))}

            {filteredKonten.length === 0 && (
              <p className="text-center text-gray-500 py-4">
                Keine Konten gefunden
              </p>
            )}
          </div>
        </div>
      )}
    </div>
  );
}

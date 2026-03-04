"use client";

import type { InvoiceData } from "@/types";
import {
  Calendar,
  CreditCard,
  FileText,
  Building,
  Hash,
  Receipt,
} from "lucide-react";

interface InvoicePreviewProps {
  data: InvoiceData;
  filename: string;
}

export function InvoicePreview({ data, filename }: InvoicePreviewProps) {
  const formatCurrency = (amount: number | null) => {
    if (amount === null) return "-";
    return new Intl.NumberFormat("de-CH", {
      style: "currency",
      currency: data.waehrung || "CHF",
    }).format(amount);
  };

  const formatDate = (dateStr: string | null) => {
    if (!dateStr) return "-";
    try {
      return new Date(dateStr).toLocaleDateString("de-CH");
    } catch {
      return dateStr;
    }
  };

  return (
    <div className="card">
      <div className="flex items-center gap-2 mb-4">
        <Receipt className="w-5 h-5 text-immotop-primary" />
        <h3 className="font-semibold text-lg">Rechnungsdaten</h3>
      </div>

      <div className="space-y-3">
        {/* Dateiname */}
        <div className="flex items-center gap-2 p-3 bg-gray-50 rounded-md">
          <FileText className="w-4 h-4 text-gray-500 flex-shrink-0" />
          <span className="text-sm font-medium truncate">{filename}</span>
        </div>

        {/* Betrag und Datum - nebeneinander */}
        <div className="grid grid-cols-2 gap-3">
          {/* Betrag */}
          <div className="p-3 bg-blue-50 rounded-md">
            <div className="flex items-center gap-2 text-sm text-gray-500 mb-1">
              <CreditCard className="w-4 h-4" />
              <span>Betrag</span>
            </div>
            <p className="text-xl font-bold text-immotop-primary break-all">
              {formatCurrency(data.bruttobetrag)}
            </p>
            {data.mwst_betrag && (
              <p className="text-xs text-gray-500 mt-1">
                inkl. {formatCurrency(data.mwst_betrag)} MwSt
              </p>
            )}
          </div>

          {/* Datum */}
          <div className="p-3 bg-gray-50 rounded-md">
            <div className="flex items-center gap-2 text-sm text-gray-500 mb-1">
              <Calendar className="w-4 h-4" />
              <span>Rechnungsdatum</span>
            </div>
            <p className="text-lg font-semibold">
              {formatDate(data.rechnungsdatum)}
            </p>
            {data.faelligkeitsdatum && (
              <p className="text-xs text-gray-500 mt-1">
                Fällig: {formatDate(data.faelligkeitsdatum)}
              </p>
            )}
          </div>
        </div>

        {/* Rechnungsnummer und IBAN */}
        <div className="grid grid-cols-2 gap-3">
          {/* Rechnungsnummer */}
          <div className="p-3 bg-gray-50 rounded-md">
            <div className="flex items-center gap-2 text-sm text-gray-500 mb-1">
              <Hash className="w-4 h-4" />
              <span>Rechnungsnr.</span>
            </div>
            <p className="font-mono text-sm break-all">
              {data.rechnungsnummer || "-"}
            </p>
          </div>

          {/* IBAN */}
          <div className="p-3 bg-gray-50 rounded-md">
            <div className="flex items-center gap-2 text-sm text-gray-500 mb-1">
              <Building className="w-4 h-4" />
              <span>IBAN</span>
            </div>
            <p className="font-mono text-xs break-all">
              {data.iban || "-"}
            </p>
          </div>
        </div>

        {/* QR-Referenz */}
        {data.qr_referenz && (
          <div className="p-3 bg-green-50 rounded-md border border-green-200">
            <div className="flex items-center gap-2 text-sm text-green-700 mb-1">
              <Hash className="w-4 h-4" />
              <span>QR-Referenz</span>
            </div>
            <p className="font-mono text-xs break-all text-green-800">
              {data.qr_referenz}
            </p>
          </div>
        )}
      </div>

      {/* OCR-Text (collapsible) */}
      <details className="mt-4">
        <summary className="cursor-pointer text-sm text-gray-500 hover:text-gray-700">
          OCR-Text anzeigen
        </summary>
        <pre className="mt-2 p-3 bg-gray-100 rounded-md text-xs overflow-x-auto max-h-48 overflow-y-auto">
          {data.raw_text}
        </pre>
      </details>
    </div>
  );
}

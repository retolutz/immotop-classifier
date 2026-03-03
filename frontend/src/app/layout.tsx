import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "Immotop Invoice Classifier",
  description: "Automatische Rechnungsklassifikation für Immotop2",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="de">
      <body className="min-h-screen">
        <header className="bg-immotop-primary text-white shadow-lg">
          <div className="max-w-7xl mx-auto px-4 py-4">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-3">
                <svg
                  className="w-8 h-8"
                  fill="none"
                  stroke="currentColor"
                  viewBox="0 0 24 24"
                >
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    strokeWidth={2}
                    d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"
                  />
                </svg>
                <div>
                  <h1 className="text-xl font-bold">Immotop Invoice Classifier</h1>
                  <p className="text-sm text-blue-200">
                    Automatische Kontozuordnung mit KI
                  </p>
                </div>
              </div>
              <div className="flex items-center gap-2 text-sm">
                <span className="px-2 py-1 bg-green-500 rounded text-xs font-medium">
                  Mock-Modus
                </span>
              </div>
            </div>
          </div>
        </header>
        <main className="max-w-7xl mx-auto px-4 py-8">{children}</main>
      </body>
    </html>
  );
}

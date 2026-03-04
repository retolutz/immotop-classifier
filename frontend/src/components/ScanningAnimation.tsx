"use client";

import { useState, useEffect } from "react";
import { Search, FileText, Brain, CheckCircle } from "lucide-react";

interface ScanningAnimationProps {
  file: File;
  onComplete?: () => void;
}

const SCAN_STEPS = [
  { icon: FileText, text: "Dokument laden...", duration: 800 },
  { icon: Search, text: "Text extrahieren...", duration: 1500 },
  { icon: Brain, text: "KI analysiert Rechnung...", duration: 2000 },
  { icon: CheckCircle, text: "Klassifikation abgeschlossen", duration: 500 },
];

export function ScanningAnimation({ file, onComplete }: ScanningAnimationProps) {
  const [previewUrl, setPreviewUrl] = useState<string | null>(null);
  const [scanProgress, setScanProgress] = useState(0);
  const [currentStep, setCurrentStep] = useState(0);
  const [scanLinePosition, setScanLinePosition] = useState(0);

  // Generate preview for PDF or image
  useEffect(() => {
    if (file.type.startsWith("image/")) {
      const url = URL.createObjectURL(file);
      setPreviewUrl(url);
      return () => URL.revokeObjectURL(url);
    } else if (file.type === "application/pdf") {
      // For PDF, we'll show a placeholder with the filename
      setPreviewUrl(null);
    }
  }, [file]);

  // Animate scan line
  useEffect(() => {
    const interval = setInterval(() => {
      setScanLinePosition((prev) => {
        if (prev >= 100) return 0;
        return prev + 2;
      });
    }, 30);
    return () => clearInterval(interval);
  }, []);

  // Progress through steps
  useEffect(() => {
    if (currentStep >= SCAN_STEPS.length) return;

    const timer = setTimeout(() => {
      setCurrentStep((prev) => prev + 1);
      setScanProgress((prev) => Math.min(100, prev + 25));
    }, SCAN_STEPS[currentStep].duration);

    return () => clearTimeout(timer);
  }, [currentStep]);

  const CurrentIcon = SCAN_STEPS[Math.min(currentStep, SCAN_STEPS.length - 1)].icon;
  const currentText = SCAN_STEPS[Math.min(currentStep, SCAN_STEPS.length - 1)].text;

  return (
    <div className="max-w-md mx-auto">
      {/* Document Preview with Scan Effect */}
      <div className="relative bg-white rounded-xl shadow-lg overflow-hidden border border-gray-200">
        {/* Preview Area */}
        <div className="relative h-64 bg-gradient-to-b from-gray-50 to-gray-100 flex items-center justify-center overflow-hidden">
          {previewUrl ? (
            <img
              src={previewUrl}
              alt="Preview"
              className="max-h-full max-w-full object-contain"
            />
          ) : (
            <div className="text-center p-6">
              <FileText className="w-20 h-20 text-red-400 mx-auto mb-3" />
              <p className="text-sm text-gray-600 font-medium truncate max-w-[200px]">
                {file.name}
              </p>
              <p className="text-xs text-gray-400 mt-1">
                {(file.size / 1024).toFixed(0)} KB
              </p>
            </div>
          )}

          {/* Scanning Line Effect */}
          <div
            className="absolute left-0 right-0 h-1 bg-gradient-to-r from-transparent via-blue-500 to-transparent opacity-80 pointer-events-none"
            style={{
              top: `${scanLinePosition}%`,
              boxShadow: "0 0 20px 5px rgba(59, 130, 246, 0.5)",
              transition: scanLinePosition === 0 ? "none" : "top 0.03s linear",
            }}
          />

          {/* Magnifying Glass */}
          <div
            className="absolute pointer-events-none"
            style={{
              left: `${30 + Math.sin(scanLinePosition * 0.1) * 20}%`,
              top: `${scanLinePosition}%`,
              transform: "translate(-50%, -50%)",
            }}
          >
            <div className="relative">
              <Search className="w-12 h-12 text-blue-600 drop-shadow-lg" />
              <div className="absolute inset-0 animate-ping">
                <Search className="w-12 h-12 text-blue-400 opacity-30" />
              </div>
            </div>
          </div>

          {/* Corner Markers */}
          <div className="absolute top-2 left-2 w-6 h-6 border-t-2 border-l-2 border-blue-500" />
          <div className="absolute top-2 right-2 w-6 h-6 border-t-2 border-r-2 border-blue-500" />
          <div className="absolute bottom-2 left-2 w-6 h-6 border-b-2 border-l-2 border-blue-500" />
          <div className="absolute bottom-2 right-2 w-6 h-6 border-b-2 border-r-2 border-blue-500" />
        </div>

        {/* Progress Section */}
        <div className="p-4 bg-white border-t border-gray-100">
          {/* Progress Bar */}
          <div className="h-2 bg-gray-200 rounded-full overflow-hidden mb-3">
            <div
              className="h-full bg-gradient-to-r from-blue-500 to-blue-600 transition-all duration-500 ease-out"
              style={{ width: `${scanProgress}%` }}
            />
          </div>

          {/* Status */}
          <div className="flex items-center justify-center gap-2">
            <CurrentIcon
              className={`w-5 h-5 ${
                currentStep >= SCAN_STEPS.length - 1
                  ? "text-green-500"
                  : "text-blue-500 animate-pulse"
              }`}
            />
            <span className="text-sm font-medium text-gray-700">
              {currentText}
            </span>
          </div>
        </div>
      </div>

      {/* Subtitle */}
      <p className="text-center text-xs text-gray-400 mt-3">
        Swiss QR-Code wird automatisch erkannt
      </p>
    </div>
  );
}

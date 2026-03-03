"use client";

interface ConfidenceIndicatorProps {
  value: number; // 0-1
  showLabel?: boolean;
  size?: "sm" | "md" | "lg";
}

export function ConfidenceIndicator({
  value,
  showLabel = true,
  size = "md",
}: ConfidenceIndicatorProps) {
  const percentage = Math.round(value * 100);

  const getColorClass = () => {
    if (value >= 0.8) return "bg-green-500";
    if (value >= 0.5) return "bg-yellow-500";
    return "bg-red-500";
  };

  const getTextColorClass = () => {
    if (value >= 0.8) return "text-green-700";
    if (value >= 0.5) return "text-yellow-700";
    return "text-red-700";
  };

  const getLabel = () => {
    if (value >= 0.9) return "Sehr sicher";
    if (value >= 0.8) return "Sicher";
    if (value >= 0.6) return "Wahrscheinlich";
    if (value >= 0.4) return "Unsicher";
    return "Sehr unsicher";
  };

  const heights = {
    sm: "h-1.5",
    md: "h-2",
    lg: "h-3",
  };

  return (
    <div className="space-y-1">
      <div className="flex items-center justify-between">
        {showLabel && (
          <span className={`text-sm font-medium ${getTextColorClass()}`}>
            {getLabel()}
          </span>
        )}
        <span className={`text-sm font-bold ${getTextColorClass()}`}>
          {percentage}%
        </span>
      </div>
      <div className={`w-full bg-gray-200 rounded-full ${heights[size]}`}>
        <div
          className={`${heights[size]} rounded-full transition-all duration-500 ${getColorClass()}`}
          style={{ width: `${percentage}%` }}
        />
      </div>
    </div>
  );
}

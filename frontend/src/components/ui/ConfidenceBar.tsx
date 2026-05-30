import { cn } from "@/lib/utils";

interface ConfidenceBarProps {
  value: number;
  className?: string;
  showLabel?: boolean;
}

function getColor(value: number): string {
  if (value >= 80) return "var(--color-success)";
  if (value >= 60) return "var(--color-warning)";
  return "var(--color-danger)";
}

export function ConfidenceBar({
  value,
  className,
  showLabel = true,
}: ConfidenceBarProps) {
  const clamped = Math.min(100, Math.max(0, value));
  const color = getColor(clamped);

  return (
    <div className={cn("flex items-center gap-2", className)}>
      <div className="h-1.5 flex-1 rounded-full bg-surface-elevated overflow-hidden">
        <div
          className="h-full rounded-full transition-all duration-500"
          style={{ width: `${clamped}%`, backgroundColor: color }}
        />
      </div>
      {showLabel && (
        <span className="text-mono text-xs w-10 text-right" style={{ color }}>
          {clamped.toFixed(0)}%
        </span>
      )}
    </div>
  );
}

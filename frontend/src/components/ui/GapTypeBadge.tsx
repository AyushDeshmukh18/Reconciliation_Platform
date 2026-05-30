import { GAP_TYPE_LABELS, type GapType } from "@/types";
import { cn, getGapTypeColor } from "@/lib/utils";

interface GapTypeBadgeProps {
  gapType: GapType | string;
  className?: string;
}

export function GapTypeBadge({ gapType, className }: GapTypeBadgeProps) {
  const color = getGapTypeColor(gapType);
  const label = GAP_TYPE_LABELS[gapType as GapType] ?? gapType;

  return (
    <span
      className={cn(
        "inline-flex items-center gap-1.5 rounded-md border px-2 py-0.5 text-xs font-medium",
        className
      )}
      style={{
        backgroundColor: `color-mix(in srgb, ${color} 12%, transparent)`,
        borderColor: `color-mix(in srgb, ${color} 25%, transparent)`,
        color,
      }}
    >
      <span
        className="h-1.5 w-1.5 rounded-full"
        style={{ backgroundColor: color }}
      />
      {label}
    </span>
  );
}

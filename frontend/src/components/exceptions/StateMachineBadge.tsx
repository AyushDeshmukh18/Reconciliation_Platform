import { RECON_STATUS_LABELS, type ReconStatus } from "@/types";
import { cn } from "@/lib/utils";

interface StateMachineBadgeProps {
  status: ReconStatus | string;
  active?: boolean;
  clickable?: boolean;
  onClick?: () => void;
}

const statusColors: Record<string, string> = {
  unprocessed: "border-muted/30 text-muted",
  matched: "border-success/30 text-success",
  partially_matched: "border-warning/30 text-warning",
  flagged: "border-danger/30 text-danger",
  manually_resolved: "border-accent/30 text-accent",
  closed: "border-border text-muted",
};

export function StateMachineBadge({
  status,
  active,
  clickable,
  onClick,
}: StateMachineBadgeProps) {
  const label = RECON_STATUS_LABELS[status as ReconStatus] ?? status;

  return (
    <button
      type="button"
      disabled={!clickable}
      onClick={onClick}
      className={cn(
        "rounded-full border px-3 py-1 text-xs font-medium transition-all",
        statusColors[status] ?? statusColors.unprocessed,
        active && "ring-2 ring-accent ring-offset-2 ring-offset-canvas bg-accent/10",
        clickable && "hover:bg-surface-hover cursor-pointer",
        !clickable && "cursor-default opacity-60"
      )}
    >
      {label}
    </button>
  );
}

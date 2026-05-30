import { RECON_STATUS_LABELS, type ReconStatus } from "@/types";
import { cn } from "@/lib/utils";

interface ReconStatusBadgeProps {
  status: ReconStatus | string;
  className?: string;
}

const statusStyles: Record<string, string> = {
  unprocessed: "bg-muted/10 text-muted border-muted/20",
  matched: "bg-success/10 text-success border-success/20",
  partially_matched: "bg-warning/10 text-warning border-warning/20",
  flagged: "bg-danger/10 text-danger border-danger/20",
  manually_resolved: "bg-accent/10 text-accent border-accent/20",
  closed: "bg-surface-elevated text-muted border-border",
};

export function ReconStatusBadge({ status, className }: ReconStatusBadgeProps) {
  const label = RECON_STATUS_LABELS[status as ReconStatus] ?? status;
  const style = statusStyles[status] ?? statusStyles.unprocessed;

  return (
    <span
      className={cn(
        "inline-flex items-center rounded-md border px-2 py-0.5 text-xs font-medium",
        style,
        className
      )}
    >
      {label}
    </span>
  );
}

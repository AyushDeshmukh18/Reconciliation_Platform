import { Link } from "react-router-dom";
import {
  CheckCircle2,
  Clock,
  Loader2,
  XCircle,
  AlertTriangle,
} from "lucide-react";
import { Card } from "@/components/ui/Card";
import { Badge } from "@/components/ui/Badge";
import { Button } from "@/components/ui/Button";
import { JobProgressBar } from "./JobProgressBar";
import { formatDate, formatCurrency } from "@/lib/utils";
import type { ReconciliationRun } from "@/types";
import { cn } from "@/lib/utils";

interface RunStatusCardProps {
  run: ReconciliationRun;
  onCancel?: () => void;
}

const statusConfig: Record<
  string,
  { icon: typeof CheckCircle2; color: string; badge: "success" | "warning" | "danger" | "accent" | "default" }
> = {
  completed: { icon: CheckCircle2, color: "text-success", badge: "success" },
  running: { icon: Loader2, color: "text-accent", badge: "accent" },
  queued: { icon: Clock, color: "text-warning", badge: "warning" },
  failed: { icon: XCircle, color: "text-danger", badge: "danger" },
};

export function RunStatusCard({ run, onCancel }: RunStatusCardProps) {
  const config = statusConfig[run.status] ?? statusConfig.queued;
  const Icon = config.icon;
  const isActive = run.status === "queued" || run.status === "running";

  return (
    <Card className="overflow-hidden">
      <div className="flex items-start justify-between gap-4">
        <div className="flex items-start gap-3">
          <div className={cn("mt-0.5", config.color)}>
            <Icon className={cn("h-5 w-5", isActive && "animate-spin")} />
          </div>
          <div>
            <div className="flex items-center gap-2">
              <Link
                to={`/exceptions?run_id=${run.run_id}`}
                className="text-subheading hover:text-accent transition-colors font-mono"
              >
                {run.run_id.slice(0, 8)}…
              </Link>
              <Badge variant={config.badge}>{run.status}</Badge>
            </div>
            <p className="text-caption mt-1">
              Started {formatDate(run.started_at_utc)} · by {run.triggered_by}
            </p>
          </div>
        </div>

        {isActive && onCancel && (
          <Button variant="ghost" size="sm" onClick={onCancel}>
            Cancel
          </Button>
        )}
      </div>

      {isActive && (
        <div className="mt-4">
          <JobProgressBar
            percent={run.progress_percent}
            message={run.progress_message ?? undefined}
          />
        </div>
      )}

      <div className="mt-4 grid grid-cols-4 gap-3 pt-4 border-t border-border">
        <div>
          <p className="text-label">Matched</p>
          <p className="text-lg font-semibold text-success">{run.matched_count}</p>
        </div>
        <div>
          <p className="text-label">Flagged</p>
          <p className="text-lg font-semibold text-danger flex items-center gap-1">
            {run.flagged_count}
            {run.flagged_count > 0 && <AlertTriangle className="h-3.5 w-3.5" />}
          </p>
        </div>
        <div>
          <p className="text-label">Unmatched</p>
          <p className="text-lg font-semibold">{run.unmatched_count}</p>
        </div>
        <div>
          <p className="text-label">Exposure</p>
          <p className="text-lg font-semibold font-mono">
            {formatCurrency(run.total_monetary_exposure_minor_units)}
          </p>
        </div>
      </div>
    </Card>
  );
}

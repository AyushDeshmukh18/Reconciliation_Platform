import { GapTypeBadge } from "@/components/ui/GapTypeBadge";
import { ReconStatusBadge } from "@/components/ui/ReconStatusBadge";
import { ConfidenceBar } from "@/components/ui/ConfidenceBar";
import { Card } from "@/components/ui/Card";
import { formatCurrency, formatDate } from "@/lib/utils";
import type { ExceptionDetail } from "@/types";

interface ExceptionDetailPanelProps {
  exception: ExceptionDetail;
}

export function ExceptionDetailPanel({ exception }: ExceptionDetailPanelProps) {
  return (
    <div className="space-y-4">
      <Card title="Exception Summary">
        <div className="space-y-4">
          <div className="flex flex-wrap gap-2">
            <GapTypeBadge gapType={exception.gap_type} />
            <ReconStatusBadge status={exception.recon_status} />
            {exception.requires_secondary_review && (
              <span className="text-xs text-warning bg-warning/10 border border-warning/20 rounded-md px-2 py-0.5">
                Secondary review required
              </span>
            )}
          </div>

          <div>
            <p className="text-label mb-1">Confidence</p>
            <ConfidenceBar value={exception.gap_confidence} />
          </div>

          <div className="grid grid-cols-2 gap-4">
            <div>
              <p className="text-label">Monetary Difference</p>
              <p className="text-lg font-mono font-semibold">
                {formatCurrency(exception.monetary_difference_minor_units)}
              </p>
            </div>
            <div>
              <p className="text-label">Created</p>
              <p className="text-sm">{formatDate(exception.created_at_utc)}</p>
            </div>
          </div>

          {exception.gap_explanation && (
            <div>
              <p className="text-label mb-1">Explanation</p>
              <p className="text-sm text-muted leading-relaxed">
                {exception.gap_explanation}
              </p>
            </div>
          )}

          {exception.resolution_suggestion && (
            <div className="rounded-md border border-accent/20 bg-accent/5 p-3">
              <p className="text-label mb-1 text-accent">Suggested Resolution</p>
              <p className="text-sm leading-relaxed">
                {exception.resolution_suggestion}
              </p>
            </div>
          )}
        </div>
      </Card>
    </div>
  );
}

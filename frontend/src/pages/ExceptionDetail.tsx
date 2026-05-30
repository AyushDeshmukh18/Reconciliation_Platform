import { Link, useParams } from "react-router-dom";
import { useQuery } from "@tanstack/react-query";
import { ArrowLeft } from "lucide-react";
import { exceptionService } from "@/services/exceptionService";
import { queryKeys } from "@/lib/queryKeys";
import { ExceptionDetailPanel } from "@/components/exceptions/ExceptionDetailPanel";
import { ResolutionForm } from "@/components/exceptions/ResolutionForm";
import { Card } from "@/components/ui/Card";
import { Skeleton } from "@/components/ui/Skeleton";
import { formatCurrency, formatDate } from "@/lib/utils";

export function ExceptionDetail() {
  const { resultId } = useParams<{ resultId: string }>();

  const { data: exception, isLoading } = useQuery({
    queryKey: queryKeys.exceptions.detail(resultId ?? ""),
    queryFn: () => exceptionService.get(resultId!),
    enabled: !!resultId,
  });

  if (isLoading) {
    return (
      <div className="space-y-4">
        <Skeleton className="h-8 w-48" />
        <div className="grid grid-cols-3 gap-4">
          <Skeleton className="h-96" />
          <Skeleton className="h-96" />
          <Skeleton className="h-96" />
        </div>
      </div>
    );
  }

  if (!exception) {
    return <p className="text-muted">Exception not found</p>;
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center gap-4">
        <Link
          to="/exceptions"
          className="flex items-center gap-2 text-sm text-muted hover:text-foreground transition-colors"
        >
          <ArrowLeft className="h-4 w-4" />
          Back to workbench
        </Link>
        <span className="text-muted">/</span>
        <span className="font-mono text-sm">{exception.result_id}</span>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Left: Platform & Bank records */}
        <div className="space-y-4">
          <Card title="Platform Transaction">
            {exception.platform_transaction ? (
              <dl className="space-y-2 text-sm">
                <div className="flex justify-between">
                  <dt className="text-muted">Merchant</dt>
                  <dd className="font-mono">{exception.platform_transaction.merchant_id}</dd>
                </div>
                <div className="flex justify-between">
                  <dt className="text-muted">Amount</dt>
                  <dd className="font-mono">
                    {formatCurrency(
                      exception.platform_transaction.amount_minor_units,
                      exception.platform_transaction.currency_code
                    )}
                  </dd>
                </div>
                <div className="flex justify-between">
                  <dt className="text-muted">Status</dt>
                  <dd>{exception.platform_transaction.transaction_status}</dd>
                </div>
                <div className="flex justify-between">
                  <dt className="text-muted">Created</dt>
                  <dd>{formatDate(exception.platform_transaction.created_at_utc)}</dd>
                </div>
              </dl>
            ) : (
              <p className="text-muted text-sm">No platform record linked</p>
            )}
          </Card>

          <Card title="Bank Settlement">
            {exception.bank_settlement ? (
              <dl className="space-y-2 text-sm">
                <div className="flex justify-between">
                  <dt className="text-muted">Reference</dt>
                  <dd className="font-mono text-xs">
                    {exception.bank_settlement.transaction_reference}
                  </dd>
                </div>
                <div className="flex justify-between">
                  <dt className="text-muted">Batch</dt>
                  <dd className="font-mono">{exception.bank_settlement.batch_id}</dd>
                </div>
                <div className="flex justify-between">
                  <dt className="text-muted">Net Settled</dt>
                  <dd className="font-mono">
                    {formatCurrency(exception.bank_settlement.net_settled_amount_minor_units)}
                  </dd>
                </div>
                <div className="flex justify-between">
                  <dt className="text-muted">Value Date</dt>
                  <dd>{formatDate(exception.bank_settlement.value_date_utc)}</dd>
                </div>
              </dl>
            ) : (
              <p className="text-muted text-sm">No bank record linked</p>
            )}
          </Card>

          {Array.isArray(exception.rule_evaluation_trace) &&
            exception.rule_evaluation_trace.length > 0 && (
              <Card title="Rule Evaluation">
                <div className="space-y-2">
                  {(exception.rule_evaluation_trace as { rule_id?: string; fired?: boolean; gap_type?: string; confidence?: number }[]).map(
                    (rule, i) => (
                      <div
                        key={i}
                        className="flex items-center justify-between text-xs rounded-md border border-border p-2"
                      >
                        <span className="font-mono">{rule.rule_id ?? `Rule ${i + 1}`}</span>
                        <span className={rule.fired ? "text-success" : "text-muted"}>
                          {rule.fired ? "FIRED" : "skipped"}
                        </span>
                      </div>
                    )
                  )}
                </div>
              </Card>
            )}
        </div>

        {/* Center: Exception detail */}
        <ExceptionDetailPanel exception={exception} />

        {/* Right: Resolution */}
        <Card title="Resolution">
          <ResolutionForm exception={exception} />
        </Card>
      </div>
    </div>
  );
}

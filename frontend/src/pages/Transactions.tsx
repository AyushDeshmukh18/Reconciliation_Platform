import { useMemo, useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { transactionService } from "@/services/transactionService";
import { queryKeys } from "@/lib/queryKeys";
import { DataTable } from "@/components/ui/DataTable";
import { Input } from "@/components/ui/Input";
import { Button } from "@/components/ui/Button";
import { Badge } from "@/components/ui/Badge";
import { Card } from "@/components/ui/Card";
import { formatCurrency, formatDate, truncateId } from "@/lib/utils";
import { cn } from "@/lib/utils";

export function Transactions() {
  const [tab, setTab] = useState<"platform" | "bank">("platform");
  const [merchantId, setMerchantId] = useState("");
  const [batchId, setBatchId] = useState("");
  const [page, setPage] = useState(1);

  const platformFilters = {
    merchant_id: merchantId || undefined,
    page,
    page_size: 25,
  };

  const bankFilters = {
    batch_id: batchId || undefined,
    page,
    page_size: 25,
  };

  const platformQuery = useQuery({
    queryKey: queryKeys.transactions.platform(platformFilters as Record<string, unknown>),
    queryFn: () => transactionService.listPlatform(platformFilters),
    enabled: tab === "platform",
  });

  const bankQuery = useQuery({
    queryKey: queryKeys.transactions.bank(bankFilters as Record<string, unknown>),
    queryFn: () => transactionService.listBank(bankFilters),
    enabled: tab === "bank",
  });

  const platformSummary = useMemo(() => {
    const rows = platformQuery.data ?? [];
    return {
      count: rows.length,
      pending: rows.filter((r) => r.transaction_status === "pending").length,
      failed: rows.filter((r) => r.transaction_status === "failed").length,
    };
  }, [platformQuery.data]);

  const bankSummary = useMemo(() => {
    const rows = bankQuery.data ?? [];
    return {
      count: rows.length,
      held: rows.filter((r) => r.settlement_status === "held").length,
      reversed: rows.filter((r) => r.settlement_status === "reversed").length,
    };
  }, [bankQuery.data]);

  const statusBadgeVariant = (status: string) => {
    if (status === "success" || status === "settled") return "success";
    if (status === "pending" || status === "held") return "warning";
    if (status === "failed" || status === "reversed" || status === "returned") return "danger";
    return "default";
  };

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-display">Transactions</h1>
        <p className="text-muted text-sm mt-1">
          Browse platform transactions and bank settlements
        </p>
      </div>

      <div className="flex flex-col gap-4 lg:flex-row lg:items-end lg:justify-between">
        <div className="flex gap-2 border-b border-border">
          {(["platform", "bank"] as const).map((t) => (
            <button
              key={t}
              onClick={() => {
                setTab(t);
                setPage(1);
              }}
              className={cn(
                "px-4 py-2 text-sm font-medium border-b-2 -mb-px transition-colors capitalize",
                tab === t
                  ? "border-accent text-accent"
                  : "border-transparent text-muted hover:text-foreground"
              )}
            >
              {t === "platform" ? "Platform" : "Bank"}
            </button>
          ))}
        </div>
        <div className="grid grid-cols-1 sm:grid-cols-3 gap-3 w-full lg:w-auto">
          <Card className="p-3">
            <p className="text-xs text-muted uppercase tracking-wide">Visible rows</p>
            <p className="text-xl font-semibold">{tab === "platform" ? platformSummary.count : bankSummary.count}</p>
          </Card>
          <Card className="p-3">
            <p className="text-xs text-muted uppercase tracking-wide">Attention</p>
            <p className="text-xl font-semibold">
              {tab === "platform" ? platformSummary.pending : bankSummary.held}
            </p>
          </Card>
          <Card className="p-3">
            <p className="text-xs text-muted uppercase tracking-wide">Alerts</p>
            <p className="text-xl font-semibold">
              {tab === "platform" ? platformSummary.failed : bankSummary.reversed}
            </p>
          </Card>
        </div>
      </div>

      {tab === "platform" ? (
        <>
          <div className="max-w-xs">
            <Input
              label="Merchant ID"
              value={merchantId}
              onChange={(e) => {
                setMerchantId(e.target.value);
                setPage(1);
              }}
              placeholder="Filter by merchant..."
            />
          </div>
          <DataTable
            data={platformQuery.data ?? []}
            loading={platformQuery.isLoading}
            keyExtractor={(r) => r.transaction_id}
            columns={[
              {
                key: "id",
                header: "ID",
                render: (r) => (
                  <span className="font-mono text-xs">
                    {truncateId(r.transaction_id)}
                  </span>
                ),
              },
              { key: "merchant_id", header: "Merchant" },
              {
                key: "amount",
                header: "Amount",
                render: (r) => (
                  <span className="font-mono">
                    {formatCurrency(r.amount_minor_units, r.currency_code)}
                  </span>
                ),
              },
              {
                key: "transaction_status",
                header: "Status",
                render: (r) => (
                  <Badge variant={statusBadgeVariant(r.transaction_status)}>
                    {r.transaction_status}
                  </Badge>
                ),
              },
              {
                key: "created_at",
                header: "Created",
                render: (r) => formatDate(r.created_at_utc),
              },
            ]}
          />
        </>
      ) : (
        <>
          <div className="max-w-xs">
            <Input
              label="Batch ID"
              value={batchId}
              onChange={(e) => {
                setBatchId(e.target.value);
                setPage(1);
              }}
              placeholder="Filter by batch..."
            />
          </div>
          <DataTable
            data={bankQuery.data ?? []}
            loading={bankQuery.isLoading}
            keyExtractor={(r) => r.settlement_id}
            columns={[
              {
                key: "id",
                header: "ID",
                render: (r) => (
                  <span className="font-mono text-xs">
                    {truncateId(r.settlement_id)}
                  </span>
                ),
              },
              { key: "batch_id", header: "Batch" },
              {
                key: "reference",
                header: "Reference",
                render: (r) => (
                  <span className="font-mono text-xs">{r.transaction_reference}</span>
                ),
              },
              {
                key: "net",
                header: "Net Settled",
                render: (r) => (
                  <span className="font-mono">
                    {formatCurrency(r.net_settled_amount_minor_units)}
                  </span>
                ),
              },
              {
                key: "settlement_status",
                header: "Status",
                render: (r) => (
                  <Badge variant={statusBadgeVariant(r.settlement_status)}>
                    {r.settlement_status}
                  </Badge>
                ),
              },
              {
                key: "value_date",
                header: "Value Date",
                render: (r) => formatDate(r.value_date_utc),
              },
            ]}
          />
        </>
      )}

      <div className="flex justify-center gap-2">
        <Button
          variant="ghost"
          size="sm"
          disabled={page <= 1}
          onClick={() => setPage((p) => p - 1)}
        >
          Previous
        </Button>
        <span className="text-sm text-muted self-center">Page {page}</span>
        <Button
          variant="ghost"
          size="sm"
          disabled={
            ((tab === "platform"
              ? platformQuery.data?.length
              : bankQuery.data?.length) ?? 0) < 25
          }
          onClick={() => setPage((p) => p + 1)}
        >
          Next
        </Button>
      </div>
    </div>
  );
}

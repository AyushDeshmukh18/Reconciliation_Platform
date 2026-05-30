import { useNavigate } from "react-router-dom";
import { DataTable } from "@/components/ui/DataTable";
import { GapTypeBadge } from "@/components/ui/GapTypeBadge";
import { ReconStatusBadge } from "@/components/ui/ReconStatusBadge";
import { ConfidenceBar } from "@/components/ui/ConfidenceBar";
import { formatCurrency, formatRelative, truncateId } from "@/lib/utils";
import type { ExceptionListItem } from "@/types";

interface ExceptionTableProps {
  data: ExceptionListItem[];
  loading?: boolean;
  selectedIds?: string[];
  onSelectionChange?: (ids: string[]) => void;
}

export function ExceptionTable({
  data,
  loading,
  selectedIds = [],
  onSelectionChange,
}: ExceptionTableProps) {
  const navigate = useNavigate();

  const toggleSelect = (id: string) => {
    if (!onSelectionChange) return;
    if (selectedIds.includes(id)) {
      onSelectionChange(selectedIds.filter((x) => x !== id));
    } else {
      onSelectionChange([...selectedIds, id]);
    }
  };

  return (
    <DataTable
      data={data}
      loading={loading}
      keyExtractor={(row) => row.result_id}
      onRowClick={(row) => navigate(`/exceptions/${row.result_id}`)}
      columns={[
        ...(onSelectionChange
          ? [
              {
                key: "select",
                header: "",
                className: "w-10",
                render: (row: ExceptionListItem) => (
                  <input
                    type="checkbox"
                    checked={selectedIds.includes(row.result_id)}
                    onChange={(e) => {
                      e.stopPropagation();
                      toggleSelect(row.result_id);
                    }}
                    onClick={(e) => e.stopPropagation()}
                    className="rounded border-border"
                  />
                ),
              },
            ]
          : []),
        {
          key: "result_id",
          header: "ID",
          render: (row) => (
            <span className="font-mono text-xs">{truncateId(row.result_id)}</span>
          ),
        },
        {
          key: "gap_type",
          header: "Gap Type",
          render: (row) => <GapTypeBadge gapType={row.gap_type} />,
        },
        {
          key: "recon_status",
          header: "Status",
          render: (row) => <ReconStatusBadge status={row.recon_status} />,
        },
        {
          key: "gap_confidence",
          header: "Confidence",
          render: (row) => (
            <ConfidenceBar value={row.gap_confidence} className="w-24" />
          ),
        },
        {
          key: "monetary_difference",
          header: "Difference",
          render: (row) => (
            <span className="font-mono">
              {formatCurrency(row.monetary_difference_minor_units)}
            </span>
          ),
        },
        {
          key: "merchant_id",
          header: "Merchant",
          render: (row) => (
            <span className="text-muted">{row.merchant_id ?? "—"}</span>
          ),
        },
        {
          key: "created_at",
          header: "Created",
          render: (row) => (
            <span className="text-muted text-xs">
              {formatRelative(row.created_at_utc)}
            </span>
          ),
        },
      ]}
    />
  );
}

import { useState } from "react";
import { useSearchParams } from "react-router-dom";
import { useQuery } from "@tanstack/react-query";
import { CheckSquare } from "lucide-react";
import { exceptionService } from "@/services/exceptionService";
import { queryKeys } from "@/lib/queryKeys";
import { ExceptionFilters } from "@/components/exceptions/ExceptionFilters";
import { ExceptionTable } from "@/components/exceptions/ExceptionTable";
import { BulkResolveModal } from "@/components/exceptions/BulkResolveModal";
import { Button } from "@/components/ui/Button";
import type { ExceptionFilters as Filters } from "@/types";

export function ExceptionWorkbench() {
  const [searchParams] = useSearchParams();
  const [selectedIds, setSelectedIds] = useState<string[]>([]);
  const [bulkOpen, setBulkOpen] = useState(false);

  const [filters, setFilters] = useState<Filters>({
    page: 1,
    page_size: 25,
    run_id: searchParams.get("run_id") ?? undefined,
    recon_status: (searchParams.get("recon_status") as Filters["recon_status"]) ?? "flagged",
  });

  const { data, isLoading } = useQuery({
    queryKey: queryKeys.exceptions.list(filters as Record<string, unknown>),
    queryFn: () => exceptionService.list(filters),
  });

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-display">Exception Workbench</h1>
          <p className="text-muted text-sm mt-1">
            Review and resolve reconciliation gaps
          </p>
        </div>
        {selectedIds.length > 0 && (
          <Button onClick={() => setBulkOpen(true)}>
            <CheckSquare className="h-4 w-4" />
            Bulk Resolve ({selectedIds.length})
          </Button>
        )}
      </div>

      <ExceptionFilters
        filters={filters}
        onChange={setFilters}
        onReset={() =>
          setFilters({ page: 1, page_size: 25, recon_status: "flagged" })
        }
      />

      <ExceptionTable
        data={data ?? []}
        loading={isLoading}
        selectedIds={selectedIds}
        onSelectionChange={setSelectedIds}
      />

      <BulkResolveModal
        open={bulkOpen}
        onClose={() => setBulkOpen(false)}
        selectedIds={selectedIds}
        onSuccess={() => setSelectedIds([])}
      />
    </div>
  );
}

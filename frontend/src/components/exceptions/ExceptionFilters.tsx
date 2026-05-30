import { GAP_TYPE_LABELS, RECON_STATUS_LABELS, type ExceptionFilters, type GapType, type ReconStatus } from "@/types";
import { Input } from "@/components/ui/Input";
import { Button } from "@/components/ui/Button";
import { cn } from "@/lib/utils";

interface ExceptionFiltersProps {
  filters: ExceptionFilters;
  onChange: (filters: ExceptionFilters) => void;
  onReset: () => void;
}

export function ExceptionFilters({
  filters,
  onChange,
  onReset,
}: ExceptionFiltersProps) {
  const update = (key: keyof ExceptionFilters, value: string) => {
    onChange({
      ...filters,
      [key]: value || undefined,
      page: 1,
    });
  };

  return (
    <div className="glass-panel p-4 space-y-4">
      <div className="flex items-center justify-between">
        <h3 className="text-subheading">Filters</h3>
        <Button variant="ghost" size="sm" onClick={onReset}>
          Reset
        </Button>
      </div>

      <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
        <div>
          <label className="text-label block mb-1.5">Gap Type</label>
          <select
            value={filters.gap_type ?? ""}
            onChange={(e) => update("gap_type", e.target.value)}
            className={cn(
              "w-full rounded-md border border-border bg-surface px-3 py-2 text-sm focus-ring"
            )}
          >
            <option value="">All types</option>
            {(Object.keys(GAP_TYPE_LABELS) as GapType[]).map((gt) => (
              <option key={gt} value={gt}>
                {GAP_TYPE_LABELS[gt]}
              </option>
            ))}
          </select>
        </div>

        <div>
          <label className="text-label block mb-1.5">Status</label>
          <select
            value={filters.recon_status ?? ""}
            onChange={(e) => update("recon_status", e.target.value)}
            className="w-full rounded-md border border-border bg-surface px-3 py-2 text-sm focus-ring"
          >
            <option value="">All statuses</option>
            {(Object.keys(RECON_STATUS_LABELS) as ReconStatus[]).map((s) => (
              <option key={s} value={s}>
                {RECON_STATUS_LABELS[s]}
              </option>
            ))}
          </select>
        </div>

        <Input
          label="Merchant ID"
          placeholder="merchant_..."
          value={filters.merchant_id ?? ""}
          onChange={(e) => update("merchant_id", e.target.value)}
        />

        <Input
          label="Run ID"
          placeholder="UUID"
          value={filters.run_id ?? ""}
          onChange={(e) => update("run_id", e.target.value)}
        />
      </div>
    </div>
  );
}

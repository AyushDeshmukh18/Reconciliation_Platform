import { Link } from "react-router-dom";
import { AlertTriangle, DollarSign, Play, TrendingUp, Upload } from "lucide-react";
import { useReconciliationRuns, useCreateRun } from "@/hooks/useReconciliation";
import { StatCard } from "@/components/ui/StatCard";
import { Button } from "@/components/ui/Button";
import { RunStatusCard } from "@/components/dashboard/RunStatusCard";
import { GapTypeChart } from "@/components/dashboard/GapTypeChart";
import { MonetaryExposureChart } from "@/components/dashboard/MonetaryExposureChart";
import { MatchRateGauge } from "@/components/dashboard/MatchRateGauge";
import { JobProgressPanel } from "@/components/dashboard/JobProgressPanel";
import { formatCurrency } from "@/lib/utils";

export function Dashboard() {
  const { data: runs, isLoading } = useReconciliationRuns();
  const createRun = useCreateRun();
  const latestRun = runs?.[0];
  const activeRun = runs?.find((run) => run.status === "queued" || run.status === "running");
  const totalFlagged = runs?.reduce((s, r) => s + r.flagged_count, 0) ?? 0;
  const totalExposure =
    runs?.reduce((s, r) => s + r.total_monetary_exposure_minor_units, 0) ?? 0;

  return (
    <div className="space-y-6">
      <div className="flex flex-col gap-4 md:flex-row md:items-center md:justify-between">
        <div>
          <h1 className="text-display">Dashboard</h1>
          <p className="text-muted text-sm mt-1">
            Overview of reconciliation operations
          </p>
        </div>
        <div className="flex flex-col items-start gap-3 sm:items-end">
          <JobProgressPanel />
          <Button
            onClick={() => createRun.mutate({})}
            loading={createRun.isPending}
            disabled={!!activeRun}
          >
            <Play className="h-4 w-4" />
            {activeRun ? "Reconciliation Running" : "Start Reconciliation"}
          </Button>
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        <StatCard
          label="Latest Match Rate"
          value={
            latestRun && latestRun.total_records > 0
              ? `${((latestRun.matched_count / latestRun.total_records) * 100).toFixed(1)}%`
              : "—"
          }
          icon={TrendingUp}
          loading={isLoading}
        />
        <StatCard
          label="Flagged Exceptions"
          value={totalFlagged.toLocaleString()}
          icon={AlertTriangle}
          changeType={totalFlagged > 0 ? "negative" : "neutral"}
          loading={isLoading}
        />
        <StatCard
          label="Total Exposure"
          value={formatCurrency(totalExposure)}
          icon={DollarSign}
          loading={isLoading}
        />
        <StatCard
          label="Reconciliation Runs"
          value={runs?.length ?? 0}
          icon={Play}
          loading={isLoading}
        />
      </div>

      {activeRun ? (
        <div className="space-y-4">
          <div className="rounded-3xl border border-accent/20 bg-accent/5 p-5">
            <p className="text-sm font-semibold text-accent">Active reconciliation in progress</p>
            <p className="text-sm text-muted mt-1">
              A reconciliation run is currently queued or running. Progress is visible live and results will refresh automatically.
            </p>
          </div>
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">
            <div className="lg:col-span-2 space-y-4">
              <RunStatusCard run={activeRun} />
            </div>
            <MatchRateGauge
              matched={activeRun.matched_count}
              total={activeRun.total_records}
            />
          </div>
        </div>
      ) : latestRun ? (
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">
          <div className="lg:col-span-2 space-y-4">
            <RunStatusCard run={latestRun} />
          </div>
          <MatchRateGauge
            matched={latestRun.matched_count}
            total={latestRun.total_records}
          />
        </div>
      ) : null}

      {latestRun && Object.keys(latestRun.gap_type_breakdown).length > 0 && (
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
          <GapTypeChart breakdown={latestRun.gap_type_breakdown} />
          <MonetaryExposureChart breakdown={latestRun.gap_type_breakdown} />
        </div>
      )}

      <Link
        to="/upload"
        className="group flex items-center justify-between rounded-xl border border-emerald-500/20 bg-gradient-to-r from-emerald-500/[0.06] to-transparent px-5 py-4 transition-colors hover:border-emerald-500/35 hover:from-emerald-500/10"
      >
        <div className="flex items-center gap-4">
          <div className="flex h-11 w-11 items-center justify-center rounded-xl bg-emerald-500/15 text-emerald-400 transition-colors group-hover:bg-emerald-500/25">
            <Upload className="h-5 w-5" />
          </div>
          <div>
            <p className="text-sm font-semibold">Upload Center</p>
            <p className="text-xs text-muted mt-0.5">
              Ingest platform & bank files in the dedicated upload workspace
            </p>
          </div>
        </div>
        <span className="text-xs font-medium text-emerald-400 opacity-0 transition-opacity group-hover:opacity-100">
          Open →
        </span>
      </Link>

      {runs && runs.length > 1 && (
        <div className="space-y-4">
          <h2 className="text-heading">Recent Runs</h2>
          {runs.slice(1, 4).map((run) => (
            <RunStatusCard key={run.run_id} run={run} />
          ))}
        </div>
      )}
    </div>
  );
}

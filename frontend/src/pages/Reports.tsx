import { useState } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { Download, FileText } from "lucide-react";
import toast from "react-hot-toast";
import { reportService } from "@/services/reportService";
import { useReconciliationRuns } from "@/hooks/useReconciliation";
import { queryKeys } from "@/lib/queryKeys";
import { getErrorMessage } from "@/services/api";
import { DataTable } from "@/components/ui/DataTable";
import { Button } from "@/components/ui/Button";
import { Card } from "@/components/ui/Card";
import { formatDate } from "@/lib/utils";
import type { ReportMeta } from "@/types";
import { useJobStore } from "@/stores/jobStore";

export function Reports() {
  const [selectedRunId, setSelectedRunId] = useState("");
  const [format, setFormat] = useState<"pdf" | "csv">("pdf");
  const queryClient = useQueryClient();

  const { data: runs } = useReconciliationRuns();
  const { data: reports, isLoading } = useQuery({
    queryKey: queryKeys.reports.all,
    queryFn: () => reportService.list(),
    refetchInterval: 10000,
  });

  const generateMutation = useMutation({
    mutationFn: () =>
      reportService.generate({ run_id: selectedRunId, format }),
    onSuccess: (data) => {
      toast.success("Report generation queued");
      queryClient.invalidateQueries({ queryKey: queryKeys.reports.all });
      if (data?.task_id) {
        addJob({
          taskId: data.task_id,
          label: `Report ${selectedRunId?.slice(0, 8) ?? "-"}`,
          type: "report",
        });
      }
    },
    onError: (err) => toast.error(getErrorMessage(err)),
  });

  const handleDownload = async (report: ReportMeta) => {
    const url = reportService.downloadUrl(report.report_id, format);
    const res = await fetch(url);
    if (!res.ok) {
      toast.error("Download failed");
      return;
    }
    const blob = await res.blob();
    const a = document.createElement("a");
    a.href = URL.createObjectURL(blob);
    a.download = `report-${report.report_id}.${format}`;
    a.click();
  };

  const addJob = useJobStore((s) => s.addJob);

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-display">Reports</h1>
        <p className="text-muted text-sm mt-1">
          Generate and download reconciliation reports
        </p>
      </div>

      <Card title="Generate Report">
        <div className="flex flex-wrap gap-3 items-end">
          <div className="flex-1 min-w-[200px]">
            <label className="text-label block mb-1.5">Reconciliation Run</label>
            <select
              value={selectedRunId}
              onChange={(e) => setSelectedRunId(e.target.value)}
              className="w-full rounded-md border border-border bg-surface px-3 py-2 text-sm focus-ring"
            >
              <option value="">Select a run...</option>
              {runs?.map((r) => (
                <option key={r.run_id} value={r.run_id}>
                  {r.run_id.slice(0, 8)}… — {r.status} ({r.flagged_count} flagged)
                </option>
              ))}
            </select>
          </div>
          <div>
            <label className="text-label block mb-1.5">Format</label>
            <select
              value={format}
              onChange={(e) => setFormat(e.target.value as "pdf" | "csv")}
              className="rounded-md border border-border bg-surface px-3 py-2 text-sm focus-ring"
            >
              <option value="pdf">PDF</option>
              <option value="csv">CSV</option>
            </select>
          </div>
          <Button
            onClick={() => generateMutation.mutate()}
            loading={generateMutation.isPending}
            disabled={!selectedRunId}
          >
            <FileText className="h-4 w-4" />
            Generate
          </Button>
        </div>
      </Card>

      <DataTable
        data={reports ?? []}
        loading={isLoading}
        keyExtractor={(r) => r.report_id}
        columns={[
          {
            key: "report_id",
            header: "Report ID",
            render: (r) => (
              <span className="font-mono text-xs">{r.report_id.slice(0, 12)}…</span>
            ),
          },
          {
            key: "run_id",
            header: "Run",
            render: (r) => (
              <span className="font-mono text-xs">{r.run_id.slice(0, 8)}…</span>
            ),
          },
          { key: "format", header: "Format" },
          {
            key: "exception_count",
            header: "Exceptions",
            render: (r) => r.exception_count,
          },
          {
            key: "generated_at",
            header: "Generated",
            render: (r) => formatDate(r.generated_at),
          },
          {
            key: "requested_by",
            header: "By",
            render: (r) => r.requested_by,
          },
          {
            key: "actions",
            header: "",
            render: (r) => (
              <Button
                variant="ghost"
                size="sm"
                onClick={(e) => {
                  e.stopPropagation();
                  handleDownload(r);
                }}
              >
                <Download className="h-4 w-4" />
              </Button>
            ),
          },
        ]}
      />
    </div>
  );
}

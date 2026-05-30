import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import toast from "react-hot-toast";
import { reconciliationService } from "@/services/reconciliationService";
import { getErrorMessage } from "@/services/api";
import { useJobStore } from "@/stores/jobStore";
import { queryKeys } from "@/lib/queryKeys";
import { generateIdempotencyKey } from "@/lib/utils";
import type { ReconciliationRunCreate } from "@/types";

export function useReconciliationRuns(page = 1) {
  return useQuery({
    queryKey: queryKeys.runs.list(page),
    queryFn: () => reconciliationService.listRuns(page),
      refetchInterval: (query) => {
      const runs = query.state.data;
      const hasActive = runs?.some(
        (r) => r.status === "queued" || r.status === "running"
      );
      return hasActive ? 5000 : false;
    },
  });
}

export function useReconciliationRun(runId: string | undefined) {
  return useQuery({
    queryKey: queryKeys.runs.detail(runId ?? ""),
    queryFn: () => reconciliationService.getRun(runId!),
    enabled: !!runId,
    refetchInterval: (query) => {
      const run = query.state.data;
      if (run?.status === "queued" || run?.status === "running") return 2000;
      return false;
    },
  });
}

export function useCreateRun() {
  const queryClient = useQueryClient();
  const addJob = useJobStore((s) => s.addJob);

  return useMutation({
    mutationFn: (body?: Partial<ReconciliationRunCreate>) =>
      reconciliationService.createRun({
        idempotency_key: body?.idempotency_key ?? generateIdempotencyKey(),
        ...body,
      }),
    onSuccess: (run) => {
      queryClient.invalidateQueries({ queryKey: queryKeys.runs.all });
      if (run.celery_task_id) {
        addJob({
          taskId: run.celery_task_id,
          label: `Reconciliation ${run.run_id.slice(0, 8)}`,
          type: "reconciliation",
        });
      }
      toast.success("Reconciliation run started");
    },
    onError: (error) => toast.error(getErrorMessage(error)),
  });
}

export function useIngestPlatform() {
  const addJob = useJobStore((s) => s.addJob);

  return useMutation({
    mutationFn: (file: File) => reconciliationService.ingestPlatform(file),
    onSuccess: (res) => {
      addJob({
        taskId: res.task_id,
        label: "Platform ingest",
        type: "ingest",
      });
      if (res.status === "completed") {
        toast.success(
          `Platform ingest complete — ${res.accepted ?? res.record_count_estimated} accepted, ${res.rejected ?? 0} rejected`
        );
        return;
      }
      toast.success("Platform file queued for ingest");
    },
    onError: (error) => toast.error(getErrorMessage(error)),
  });
}

export function useIngestBank() {
  const addJob = useJobStore((s) => s.addJob);

  return useMutation({
    mutationFn: (file: File) => reconciliationService.ingestBank(file),
    onSuccess: (res) => {
      addJob({
        taskId: res.task_id,
        label: "Bank ingest",
        type: "ingest",
      });
      if (res.status === "completed") {
        toast.success(
          `Bank ingest complete — ${res.accepted ?? res.record_count_estimated} accepted, ${res.rejected ?? 0} rejected`
        );
        return;
      }
      toast.success("Bank file queued for ingest");
    },
    onError: (error) => toast.error(getErrorMessage(error)),
  });
}

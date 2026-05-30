import { useEffect } from "react";
import { useQueryClient } from "@tanstack/react-query";
import { API_BASE } from "@/services/api";
import { useJobStore } from "@/stores/jobStore";
import { queryKeys } from "@/lib/queryKeys";
import type { JobProgress } from "@/types";

export function useJobProgress(taskId: string | null | undefined, enabled = true) {
  const { updateProgress, removeJob } = useJobStore();
  const queryClient = useQueryClient();

  useEffect(() => {
    if (!taskId || !enabled || taskId.startsWith("sync-")) return;

    const base = API_BASE || "";
    const url = `${base}/api/v1/jobs/${taskId}/progress`;
    const eventSource = new EventSource(url);

    eventSource.onmessage = (event) => {
      try {
        const progress = JSON.parse(event.data) as JobProgress;
        updateProgress(taskId, progress);
        if (progress.status === "SUCCESS") {
          queryClient.invalidateQueries({ queryKey: queryKeys.runs.all });
          queryClient.invalidateQueries({ queryKey: ["runs"] });
          queryClient.invalidateQueries({ queryKey: ["transactions"] });
          queryClient.invalidateQueries({ queryKey: ["exceptions"] });
          queryClient.invalidateQueries({ queryKey: queryKeys.exceptions.all });
          queryClient.invalidateQueries({ queryKey: queryKeys.reports.all });
          queryClient.invalidateQueries({ queryKey: queryKeys.audit.all });
          eventSource.close();
          setTimeout(() => removeJob(taskId), 3000);
        } else if (progress.status === "FAILURE") {
          queryClient.invalidateQueries({ queryKey: queryKeys.runs.all });
          queryClient.invalidateQueries({ queryKey: ["runs"] });
          queryClient.invalidateQueries({ queryKey: queryKeys.audit.all });
          eventSource.close();
          setTimeout(() => removeJob(taskId), 3000);
        }
      } catch {
        /* ignore parse errors */
      }
    };

    eventSource.onerror = () => {
      eventSource.close();
    };

    return () => {
      eventSource.close();
    };
  }, [taskId, enabled, updateProgress, removeJob, queryClient]);

  return useJobStore((s) => (taskId ? s.progress[taskId] : undefined));
}

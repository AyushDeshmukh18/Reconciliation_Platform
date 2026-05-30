import { useState } from "react";
import { Loader2, ChevronDown, ChevronUp } from "lucide-react";
import { useJobStore } from "@/stores/jobStore";
import { useJobProgress } from "@/hooks/useJobProgress";
import { JobProgressBar } from "./JobProgressBar";

function ActiveJobItem({ taskId, label }: { taskId: string; label: string }) {
  const progress = useJobProgress(taskId);

  return (
    <div className="px-3 py-2">
      <p className="text-xs font-medium mb-1.5 truncate">{label}</p>
      <JobProgressBar
        percent={progress?.progress_percent ?? 0}
        message={progress?.message}
        status={progress?.status}
      />
    </div>
  );
}

export function JobProgressPanel() {
  const [open, setOpen] = useState(false);
  const activeJobs = useJobStore((s) => s.activeJobs);

  if (activeJobs.length === 0) return null;

  return (
    <div className="relative">
      <button
        onClick={() => setOpen(!open)}
        className="flex items-center gap-2 rounded-md border border-accent/30 bg-accent/10 px-3 py-1.5 text-sm text-accent"
      >
        <Loader2 className="h-3.5 w-3.5 animate-spin" />
        <span>{activeJobs.length} active</span>
        {open ? <ChevronUp className="h-3.5 w-3.5" /> : <ChevronDown className="h-3.5 w-3.5" />}
      </button>

      {open && (
        <div className="absolute right-0 top-full mt-2 w-72 rounded-lg border border-border bg-surface-elevated shadow-lg animate-slide-up">
          <div className="border-b border-border px-3 py-2">
            <p className="text-xs font-medium text-muted">Background Jobs</p>
          </div>
          <div className="max-h-64 overflow-y-auto divide-y divide-border-subtle">
            {activeJobs.map((job) => (
              <ActiveJobItem key={job.taskId} taskId={job.taskId} label={job.label} />
            ))}
          </div>
        </div>
      )}
    </div>
  );
}

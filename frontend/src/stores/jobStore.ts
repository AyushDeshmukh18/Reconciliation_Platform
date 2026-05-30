import { create } from "zustand";
import type { JobProgress } from "@/types";

interface ActiveJob {
  taskId: string;
  label: string;
  type: "reconciliation" | "ingest" | "report";
}

interface JobState {
  activeJobs: ActiveJob[];
  progress: Record<string, JobProgress>;
  addJob: (job: ActiveJob) => void;
  removeJob: (taskId: string) => void;
  updateProgress: (taskId: string, progress: JobProgress) => void;
  clearCompleted: () => void;
}

export const useJobStore = create<JobState>((set) => ({
  activeJobs: [],
  progress: {},
  addJob: (job) =>
    set((state) => ({
      activeJobs: state.activeJobs.some((j) => j.taskId === job.taskId)
        ? state.activeJobs
        : [...state.activeJobs, job],
    })),
  removeJob: (taskId) =>
    set((state) => ({
      activeJobs: state.activeJobs.filter((j) => j.taskId !== taskId),
      progress: Object.fromEntries(
        Object.entries(state.progress).filter(([id]) => id !== taskId)
      ),
    })),
  updateProgress: (taskId, progress) =>
    set((state) => ({
      progress: { ...state.progress, [taskId]: progress },
    })),
  clearCompleted: () =>
    set((state) => {
      const completed = new Set(
        Object.entries(state.progress)
          .filter(([, p]) => p.status === "SUCCESS" || p.status === "FAILURE")
          .map(([id]) => id)
      );
      return {
        activeJobs: state.activeJobs.filter((j) => !completed.has(j.taskId)),
        progress: Object.fromEntries(
          Object.entries(state.progress).filter(([id]) => !completed.has(id))
        ),
      };
    }),
}));

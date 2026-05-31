export const queryKeys = {
  runs: {
    all: ["runs"] as const,
    list: (page: number) => ["runs", "list", page] as const,
    detail: (runId: string) => ["runs", "detail", runId] as const,
  },
  exceptions: {
    all: ["exceptions"] as const,
    list: (filters: Record<string, unknown>) =>
      ["exceptions", "list", filters] as const,
    detail: (resultId: string) => ["exceptions", "detail", resultId] as const,
  },
  transactions: {
    platform: (filters: Record<string, unknown>) =>
      ["transactions", "platform", filters] as const,
    bank: (filters: Record<string, unknown>) =>
      ["transactions", "bank", filters] as const,
  },
  reports: {
    all: ["reports"] as const,
  },
  audit: {
    all: ["audit"] as const,
    list: (filters: Record<string, unknown>) =>
      ["audit", "list", filters] as const,
  },
  jobs: {
    progress: (taskId: string) => ["jobs", "progress", taskId] as const,
  },
};

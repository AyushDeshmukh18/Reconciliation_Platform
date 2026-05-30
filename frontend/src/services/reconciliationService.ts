import { api } from "./api";
import type {
  IngestResponse,
  ReconciliationRun,
  ReconciliationRunCreate,
} from "@/types";

export const reconciliationService = {
  listRuns: async (page = 1, pageSize = 20): Promise<ReconciliationRun[]> => {
    const { data } = await api.get<ReconciliationRun[]>("/reconciliation/runs", {
      params: { page, page_size: pageSize },
    });
    return data;
  },

  getRun: async (runId: string): Promise<ReconciliationRun> => {
    const { data } = await api.get<ReconciliationRun>(
      `/reconciliation/runs/${runId}`
    );
    return data;
  },

  createRun: async (body: ReconciliationRunCreate): Promise<ReconciliationRun> => {
    const { data } = await api.post<ReconciliationRun>(
      "/reconciliation/runs",
      body
    );
    return data;
  },

  cancelRun: async (runId: string): Promise<void> => {
    await api.post(`/reconciliation/runs/${runId}/cancel`);
  },

  ingestPlatform: async (file: File): Promise<IngestResponse> => {
    const form = new FormData();
    form.append("file", file);
    const { data } = await api.post<IngestResponse>(
      "/reconciliation/ingest/platform",
      form
    );
    return data;
  },

  ingestBank: async (file: File): Promise<IngestResponse> => {
    const form = new FormData();
    form.append("file", file);
    const { data } = await api.post<IngestResponse>(
      "/reconciliation/ingest/bank",
      form
    );
    return data;
  },
};

import { api, API_BASE } from "./api";
import type { ReportGenerateRequest, ReportMeta } from "@/types";

export const reportService = {
  list: async (): Promise<ReportMeta[]> => {
    const { data } = await api.get<ReportMeta[]>("/reports");
    return data;
  },

  generate: async (
    body: ReportGenerateRequest
  ): Promise<{ task_id: string; status: string }> => {
    const { data } = await api.post<{ task_id: string; status: string }>(
      "/reports/generate",
      body
    );
    return data;
  },

  downloadUrl: (reportId: string, fileType: "pdf" | "csv" = "pdf"): string => {
    return `${API_BASE}/api/v1/reports/${reportId}/download?file_type=${fileType}`;
  },
};

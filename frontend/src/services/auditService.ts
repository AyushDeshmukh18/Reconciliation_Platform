import { api } from "./api";
import type { AuditLogEntry } from "@/types";

export interface AuditFilters {
  event_type?: string;
  entity_id?: string;
  actor?: string;
  page?: number;
  page_size?: number;
}

export const auditService = {
  list: async (filters: AuditFilters = {}): Promise<AuditLogEntry[]> => {
    const { data } = await api.get<AuditLogEntry[]>("/audit", { params: filters });
    return data;
  },

  byEntity: async (entityId: string): Promise<AuditLogEntry[]> => {
    const { data } = await api.get<AuditLogEntry[]>(`/audit/entity/${entityId}`);
    return data;
  },

  exportUrl: (): string => {
    return `${api.defaults.baseURL}/audit/export`;
  },
};

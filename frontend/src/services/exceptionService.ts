import { api } from "./api";
import type {
  BulkResolveRequest,
  ExceptionDetail,
  ExceptionFilters,
  ExceptionListItem,
  ResolutionNote,
  ResolutionNoteCreate,
  StatusUpdateRequest,
} from "@/types";

export const exceptionService = {
  list: async (filters: ExceptionFilters = {}): Promise<ExceptionListItem[]> => {
    const { data } = await api.get<ExceptionListItem[]>("/exceptions", {
      params: filters,
    });
    return data;
  },

  get: async (resultId: string): Promise<ExceptionDetail> => {
    const { data } = await api.get<ExceptionDetail>(`/exceptions/${resultId}`);
    return data;
  },

  updateStatus: async (
    resultId: string,
    body: StatusUpdateRequest
  ): Promise<ExceptionDetail> => {
    const { data } = await api.patch<ExceptionDetail>(
      `/exceptions/${resultId}/status`,
      body
    );
    return data;
  },

  addNote: async (
    resultId: string,
    body: ResolutionNoteCreate
  ): Promise<ResolutionNote> => {
    const { data } = await api.post<ResolutionNote>(
      `/exceptions/${resultId}/notes`,
      body
    );
    return data;
  },

  listNotes: async (resultId: string): Promise<ResolutionNote[]> => {
    const { data } = await api.get<ResolutionNote[]>(
      `/exceptions/${resultId}/notes`
    );
    return data;
  },

  bulkResolve: async (body: BulkResolveRequest): Promise<{ resolved: number }> => {
    const { data } = await api.post<{ resolved: number }>(
      "/exceptions/bulk-resolve",
      body
    );
    return data;
  },

  suggestResolution: async (resultId: string): Promise<{ suggestion: string }> => {
    const { data } = await api.get<{ suggestion: string }>(
      `/exceptions/${resultId}/suggest-resolution`
    );
    return data;
  },
};

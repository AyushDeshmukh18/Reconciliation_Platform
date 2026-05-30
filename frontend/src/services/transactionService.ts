import { api } from "./api";
import type { BankSettlement, PlatformTransaction } from "@/types";

export interface TransactionFilters {
  merchant_id?: string;
  status?: string;
  batch_id?: string;
  page?: number;
  page_size?: number;
}

export const transactionService = {
  listPlatform: async (
    filters: TransactionFilters = {}
  ): Promise<PlatformTransaction[]> => {
    const { data } = await api.get<PlatformTransaction[]>(
      "/transactions/platform",
      { params: filters }
    );
    return data;
  },

  listBank: async (filters: TransactionFilters = {}): Promise<BankSettlement[]> => {
    const { data } = await api.get<BankSettlement[]>("/transactions/bank", {
      params: filters,
    });
    return data;
  },
};

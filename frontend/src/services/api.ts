import axios from "axios";

export const API_BASE = import.meta.env.VITE_API_BASE_URL || "";
const API_PREFIX = `${API_BASE}/api/v1`;

export const api = axios.create({
  baseURL: API_PREFIX,
  headers: { "Content-Type": "application/json" },
});

api.interceptors.request.use((config) => {
  if (config.data instanceof FormData) {
    delete config.headers["Content-Type"];
  }
  return config;
});

export function getErrorMessage(error: unknown): string {
  if (axios.isAxiosError(error)) {
    return error.response?.data?.detail ?? error.response?.data?.message ?? error.message;
  }
  if (error instanceof Error) return error.message;
  return "An unexpected error occurred";
}

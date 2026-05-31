import axios from "axios";

export const API_BASE = import.meta.env.VITE_API_BASE_URL || "";
const API_PREFIX = `${API_BASE}/api/v1`;

console.log("📡 API Configuration:");
console.log("  VITE_API_BASE_URL:", import.meta.env.VITE_API_BASE_URL);
console.log("  API_BASE:", API_BASE);
console.log("  API_PREFIX:", API_PREFIX);

export const api = axios.create({
  baseURL: API_PREFIX,
  headers: { "Content-Type": "application/json" },
});

// Request interceptor for logging
api.interceptors.request.use((config) => {
  console.log(`🚀 Request: ${config.method?.toUpperCase()} ${config.url}`);
  if (config.data instanceof FormData) {
    delete config.headers["Content-Type"];
  }
  return config;
});

// Response interceptor for logging
api.interceptors.response.use(
  (response) => {
    console.log(`✅ Response: ${response.config.method?.toUpperCase()} ${response.config.url}`, response.data);
    return response;
  },
  (error) => {
    console.error(`❌ Error: ${error.config?.method?.toUpperCase()} ${error.config?.url}`, error);
    return Promise.reject(error);
  }
);

export function getErrorMessage(error: unknown): string {
  if (axios.isAxiosError(error)) {
    return error.response?.data?.detail ?? error.response?.data?.message ?? error.message;
  }
  if (error instanceof Error) return error.message;
  return "An unexpected error occurred";
}

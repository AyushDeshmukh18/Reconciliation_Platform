import axios from "axios";

const rawApiUrl = import.meta.env.VITE_API_URL;
const isProduction = import.meta.env.PROD;

console.log("🚀 Frontend API Configuration:");
console.log(`  - Mode: ${isProduction ? "PRODUCTION" : "DEVELOPMENT"}`);
console.log(`  - VITE_API_URL: ${rawApiUrl || "NOT SET"}`);

if (isProduction && !rawApiUrl) {
  const errorMsg = "CRITICAL ERROR: VITE_API_URL is not set in production!";
  console.error(errorMsg);
  alert(errorMsg);
  throw new Error(errorMsg);
}

const API_BASE = rawApiUrl || "";
const API_PREFIX = `${API_BASE}/api/v1`;

console.log(`  - Final API Prefix: ${API_PREFIX}`);

export const api = axios.create({
  baseURL: API_PREFIX,
  headers: { "Content-Type": "application/json" },
});

// Request interceptor for logging
api.interceptors.request.use((config) => {
  console.log(`📤 Outgoing Request: ${config.method?.toUpperCase()} ${config.baseURL}${config.url}`);
  if (config.data instanceof FormData) {
    delete config.headers["Content-Type"];
  }
  return config;
});

// Response interceptor for logging
api.interceptors.response.use(
  (response) => {
    console.log(`✅ Response: ${response.config.method?.toUpperCase()} ${response.config.baseURL}${response.config.url}`, response.data);
    return response;
  },
  (error) => {
    console.error(`❌ ERROR: ${error.config?.method?.toUpperCase()} ${error.config?.baseURL}${error.config?.url}`, error);
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

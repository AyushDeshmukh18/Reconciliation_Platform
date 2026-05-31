import { clsx, type ClassValue } from "clsx";
import { twMerge } from "tailwind-merge";

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}

export function formatCurrency(minorUnits: number, currency = "USD"): string {
  const amount = minorUnits / 100;
  return new Intl.NumberFormat("en-US", {
    style: "currency",
    currency,
    minimumFractionDigits: 2,
  }).format(amount);
}

export function formatDate(iso: string): string {
  return new Intl.DateTimeFormat("en-US", {
    month: "short",
    day: "numeric",
    year: "numeric",
    hour: "2-digit",
    minute: "2-digit",
    timeZone: "UTC",
    timeZoneName: "short",
  }).format(new Date(iso));
}

export function formatRelative(iso: string): string {
  const diff = Date.now() - new Date(iso).getTime();
  const minutes = Math.floor(diff / 60000);
  if (minutes < 1) return "just now";
  if (minutes < 60) return `${minutes}m ago`;
  const hours = Math.floor(minutes / 60);
  if (hours < 24) return `${hours}h ago`;
  const days = Math.floor(hours / 24);
  return `${days}d ago`;
}

export function truncateId(id: string, length = 8): string {
  return id.slice(0, length);
}

export function generateIdempotencyKey(): string {
  return `run-${Date.now()}-${Math.random().toString(36).slice(2, 9)}`;
}

export function getGapTypeColor(gapType: string): string {
  const colors: Record<string, string> = {
    timing_gap: "var(--gap-timing)",
    rounding_difference: "var(--gap-rounding)",
    duplicate_entry: "var(--gap-duplicate)",
    orphan_refund: "var(--gap-orphan)",
    partial_settlement: "var(--gap-partial)",
    failed_reversal: "var(--gap-failed)",
    split_settlement: "var(--gap-split)",
    stale_retry: "var(--gap-stale)",
    settlement_truncation: "var(--gap-truncation)",
    status_mismatch: "var(--gap-status)",
    idempotency_failure: "var(--gap-idempotency)",
    unclassified: "var(--gap-unclassified)",
  };
  return colors[gapType] ?? "var(--gap-unclassified)";
}

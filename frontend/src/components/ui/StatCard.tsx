import type { LucideIcon } from "lucide-react";
import { cn } from "@/lib/utils";
import { Skeleton } from "./Skeleton";

interface StatCardProps {
  label: string;
  value: string | number;
  change?: string;
  changeType?: "positive" | "negative" | "neutral";
  icon?: LucideIcon;
  loading?: boolean;
  className?: string;
}

export function StatCard({
  label,
  value,
  change,
  changeType = "neutral",
  icon: Icon,
  loading,
  className,
}: StatCardProps) {
  if (loading) {
    return (
      <div className={cn("glass-panel p-5", className)}>
        <Skeleton className="h-3 w-20 mb-3" />
        <Skeleton className="h-8 w-32 mb-2" />
        <Skeleton className="h-3 w-16" />
      </div>
    );
  }

  const changeColors = {
    positive: "text-success",
    negative: "text-danger",
    neutral: "text-muted",
  };

  return (
    <div className={cn("glass-panel p-5 transition-colors hover:bg-surface-elevated", className)}>
      <div className="flex items-start justify-between">
        <p className="text-label">{label}</p>
        {Icon && (
          <div className="rounded-md bg-accent/10 p-2">
            <Icon className="h-4 w-4 text-accent" />
          </div>
        )}
      </div>
      <p className="mt-2 text-2xl font-semibold tracking-tight">{value}</p>
      {change && (
        <p className={cn("mt-1 text-caption", changeColors[changeType])}>
          {change}
        </p>
      )}
    </div>
  );
}

import { cn } from "@/lib/utils";

interface JobProgressBarProps {
  percent: number;
  message?: string;
  status?: string;
  className?: string;
}

export function JobProgressBar({
  percent,
  message,
  status,
  className,
}: JobProgressBarProps) {
  const isFailed = status === "FAILURE";
  const isComplete = status === "SUCCESS";

  return (
    <div className={cn("space-y-1.5", className)}>
      <div className="flex items-center justify-between text-xs">
        <span className="text-muted truncate flex-1 mr-2">
          {message ?? "Processing..."}
        </span>
        <span className="font-mono text-foreground">{percent.toFixed(0)}%</span>
      </div>
      <div className="h-1.5 rounded-full bg-surface-elevated overflow-hidden">
        <div
          className={cn(
            "h-full rounded-full transition-all duration-500",
            isFailed && "bg-danger",
            isComplete && "bg-success",
            !isFailed && !isComplete && "bg-accent"
          )}
          style={{ width: `${Math.min(100, percent)}%` }}
        />
      </div>
    </div>
  );
}

import { useCallback, useRef, useState } from "react";
import { Upload, FileSpreadsheet } from "lucide-react";
import { cn } from "@/lib/utils";

interface FileDropZoneProps {
  accept?: string;
  label: string;
  description?: string;
  onFile: (file: File) => void;
  loading?: boolean;
  variant?: "default" | "upload";
}

export function FileDropZone({
  accept = ".csv",
  label,
  description,
  onFile,
  loading,
  variant = "default",
}: FileDropZoneProps) {
  const [dragging, setDragging] = useState(false);
  const inputRef = useRef<HTMLInputElement>(null);

  const handleFile = useCallback(
    (file: File) => {
      onFile(file);
      if (inputRef.current) inputRef.current.value = "";
    },
    [onFile]
  );

  const handleDrop = useCallback(
    (e: React.DragEvent) => {
      e.preventDefault();
      setDragging(false);
      const file = e.dataTransfer.files[0];
      if (file) handleFile(file);
    },
    [handleFile]
  );

  return (
    <div
      onDragOver={(e) => {
        e.preventDefault();
        setDragging(true);
      }}
      onDragLeave={() => setDragging(false)}
      onDrop={handleDrop}
      className={cn(
        "relative text-center transition-all duration-200",
        variant === "upload"
          ? "rounded-xl border-2 border-dashed p-10 min-h-[200px] flex items-center justify-center"
          : "rounded-lg border-2 border-dashed p-8",
        dragging
          ? variant === "upload"
            ? "border-emerald-400 bg-emerald-500/10 scale-[1.01]"
            : "border-accent bg-accent/5"
          : variant === "upload"
            ? "border-white/[0.1] hover:border-emerald-500/40 hover:bg-emerald-500/[0.03]"
            : "border-border hover:border-accent/50 hover:bg-surface-hover"
      )}
    >
      <input
        ref={inputRef}
        type="file"
        accept={accept}
        disabled={loading}
        onChange={(e) => {
          const file = e.target.files?.[0];
          if (file) handleFile(file);
        }}
        className="absolute inset-0 cursor-pointer opacity-0"
      />
      <div className="flex flex-col items-center gap-3 pointer-events-none">
        {loading ? (
          <div className="h-10 w-10 animate-spin rounded-full border-2 border-accent border-t-transparent" />
        ) : (
          <div className={cn(
            "rounded-full p-3",
            variant === "upload" ? "bg-emerald-500/15" : "bg-accent/10"
          )}>
            <Upload className={cn("h-6 w-6", variant === "upload" ? "text-emerald-400" : "text-accent")} />
          </div>
        )}
        <div>
          <p className="text-sm font-medium">{label}</p>
          {description && (
            <p className="text-caption mt-1">{description}</p>
          )}
        </div>
        <div className="flex items-center gap-1 text-xs text-muted">
          <FileSpreadsheet className="h-3.5 w-3.5" />
          CSV · JSONL · up to 100MB
        </div>
      </div>
    </div>
  );
}

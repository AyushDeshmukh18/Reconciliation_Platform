import { useCallback, useRef, useState } from "react";
import { Link } from "react-router-dom";
import {
  Building2,
  CheckCircle2,
  Database,
  Download,
  FileSpreadsheet,
  Hash,
  Landmark,
  Loader2,
  Play,
  Shield,
  Upload,
} from "lucide-react";
import { cn } from "@/lib/utils";
import { useCreateRun, useIngestBank, useIngestPlatform } from "@/hooks/useReconciliation";

type UploadKind = "platform" | "bank";
type UploadState = {
  file: File | null;
  status: "idle" | "ready" | "uploading" | "success" | "error";
  message: string;
};

const sampleFiles = {
  platform: [
    { name: "Platform Sample 1", path: "/samples/platform_transactions.csv" },
    { name: "Platform Sample 2", path: "/samples/platform_transactions_01.csv" },
    { name: "Platform Sample 3", path: "/samples/platform_transactions_02.csv" },
    { name: "Platform Sample 4", path: "/samples/platform_transactions_03.csv" },
    { name: "Platform Sample 5", path: "/samples/platform_transactions_04.csv" },
  ],
  bank: [
    { name: "Bank Sample 1", path: "/samples/bank_settlements.csv" },
    { name: "Bank Sample 2", path: "/samples/bank_settlements_01.csv" },
    { name: "Bank Sample 3", path: "/samples/bank_settlements_02.csv" },
    { name: "Bank Sample 4", path: "/samples/bank_settlements_03.csv" },
    { name: "Bank Sample 5", path: "/samples/bank_settlements_04.csv" },
  ],
};

const steps = [
  {
    num: "01",
    title: "Platform transactions",
    desc: "CSV or JSONL with transaction_id, amount, merchant_id, timestamp, status.",
    icon: Building2,
  },
  {
    num: "02",
    title: "Bank settlements",
    desc: "CSV or JSONL with batch_id, transaction_reference, settled_amount, value_date.",
    icon: Landmark,
  },
  {
    num: "03",
    title: "Trigger reconciliation",
    desc: "Multi-pass matching runs automatically. Track progress via live SSE.",
    icon: Play,
  },
];

function UploadCard({
  kind,
  title,
  subtitle,
  description,
  icon: Icon,
  state,
  onSelect,
  onUpload,
}: {
  kind: UploadKind;
  title: string;
  subtitle: string;
  description: string;
  icon: typeof Building2;
  state: UploadState;
  onSelect: (kind: UploadKind, file: File) => void;
  onUpload: (kind: UploadKind) => void;
}) {
  const inputRef = useRef<HTMLInputElement>(null);
  const [dragging, setDragging] = useState(false);
  const isUploading = state.status === "uploading";

  const chooseFile = useCallback(
    (file: File | undefined) => {
      if (!file) return;
      onSelect(kind, file);
      if (inputRef.current) inputRef.current.value = "";
    },
    [kind, onSelect]
  );

  return (
    <div
      className={cn(
        "rounded-2xl border p-1",
        "border-blue-500/15 bg-gradient-to-b from-blue-500/[0.04] to-transparent"
      )}
    >
      <div className="rounded-[14px] bg-surface/80 p-5">
        <div className="mb-4 flex items-center gap-3">
          <div
            className={cn(
              "flex h-10 w-10 items-center justify-center rounded-xl",
              "bg-blue-500/15"
            )}
          >
            <Icon className="h-5 w-5 text-blue-400" />
          </div>
          <div className="min-w-0">
            <h2 className="font-semibold">{title}</h2>
            <p className="truncate text-xs text-muted">{subtitle}</p>
          </div>
        </div>

        <div
          onDragOver={(event) => {
            event.preventDefault();
            setDragging(true);
          }}
          onDragLeave={() => setDragging(false)}
          onDrop={(event) => {
            event.preventDefault();
            setDragging(false);
            chooseFile(event.dataTransfer.files[0]);
          }}
          className={cn(
            "relative flex min-h-[214px] items-center justify-center rounded-xl border-2 border-dashed p-8 text-center transition-all",
            dragging
              ? "border-blue-400 bg-blue-500/10"
              : "border-white/[0.1] hover:border-blue-500/40 hover:bg-white/[0.02]"
          )}
        >
          <input
            ref={inputRef}
            type="file"
            accept=".csv,.jsonl,.ndjson"
            className="absolute inset-0 cursor-pointer opacity-0"
            onChange={(event) => chooseFile(event.target.files?.[0])}
          />

          <div className="pointer-events-none flex flex-col items-center gap-3">
            <div
              className={cn(
                "rounded-full p-3",
                "bg-blue-500/15"
              )}
            >
              {isUploading ? (
                <Loader2 className="h-6 w-6 animate-spin text-foreground" />
              ) : (
                <Upload className="h-6 w-6 text-blue-400" />
              )}
            </div>
            <div>
              <p className="text-sm font-medium">
                {state.file ? state.file.name : `Drop ${description}`}
              </p>
              <p className="mt-1 text-caption">CSV, JSONL, or NDJSON up to 100MB</p>
            </div>
            <div className="flex items-center gap-1 text-xs text-muted">
              <FileSpreadsheet className="h-3.5 w-3.5" />
              {state.file ? `${Math.max(1, Math.round(state.file.size / 1024))} KB selected` : "Ready for file selection"}
            </div>
          </div>
        </div>

        <div className="mt-4 flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
          <p
            className={cn(
              "min-h-5 text-xs",
              state.status === "success" && "text-blue-400",
              state.status === "error" && "text-red-400",
              (state.status === "idle" || state.status === "ready" || state.status === "uploading") &&
                "text-muted"
            )}
          >
            {state.message}
          </p>
          <button
            type="button"
            disabled={!state.file || isUploading}
            onClick={() => onUpload(kind)}
            className={cn(
              "inline-flex h-9 items-center justify-center gap-2 rounded-md px-4 text-sm font-medium transition-colors disabled:pointer-events-none disabled:opacity-50",
              "border border-blue-500/30 bg-blue-600 text-white hover:bg-blue-500"
            )}
          >
            {isUploading ? <Loader2 className="h-4 w-4 animate-spin" /> : <Upload className="h-4 w-4" />}
            Upload
          </button>
        </div>
      </div>
    </div>
  );
}

function SampleFileList({
  title,
  files,
}: {
  title: string;
  files: Array<{ name: string; path: string }>;
}) {
  return (
    <div className="rounded-2xl border border-border/70 bg-surface/80 p-5">
      <div className="mb-4 flex items-center justify-between gap-3">
        <div>
          <p className="text-sm font-semibold">{title}</p>
          <p className="text-xs text-muted mt-1">
            Download ready-to-use sample files for quick ingestion.
          </p>
        </div>
        <Download className="h-4 w-4 text-blue-400" />
      </div>
      <div className="space-y-2">
        {files.map((file) => (
          <a
            key={file.path}
            href={file.path}
            download
            className="flex items-center justify-between rounded-xl border border-border/60 bg-surface px-4 py-3 text-sm transition-colors hover:border-blue-400/40 hover:bg-blue-500/5"
          >
            <span>{file.name}</span>
            <span className="text-xs text-blue-400">Download</span>
          </a>
        ))}
      </div>
    </div>
  );
}

export function UploadCenter() {
  const [uploads, setUploads] = useState<Record<UploadKind, UploadState>>({
    platform: {
      file: null,
      status: "idle",
      message: "No platform file selected.",
    },
    bank: {
      file: null,
      status: "idle",
      message: "No bank settlement file selected.",
    },
  });
  const ingestPlatform = useIngestPlatform();
  const ingestBank = useIngestBank();
  const createRun = useCreateRun();

  const selectFile = useCallback((kind: UploadKind, file: File) => {
    setUploads((current) => ({
      ...current,
      [kind]: {
        file,
        status: "ready",
        message: `${file.name} is ready to upload.`,
      },
    }));
  }, []);

  const runUpload = useCallback(async (kind: UploadKind) => {
    const file = uploads[kind].file;
    if (!file) return;

    setUploads((current) => ({
      ...current,
      [kind]: {
        ...current[kind],
        status: "uploading",
        message: "Uploading to ingestion API...",
      },
    }));

    try {
      if (kind === "platform") {
        await ingestPlatform.mutateAsync(file);
      } else {
        await ingestBank.mutateAsync(file);
      }
      setUploads((current) => ({
        ...current,
        [kind]: {
          ...current[kind],
          status: "success",
          message: "Upload accepted and queued for processing.",
        },
      }));
    } catch (error: any) {
      setUploads((current) => ({
        ...current,
        [kind]: {
          ...current[kind],
          status: "error",
          message: error?.response?.data?.detail ?? error?.message ?? "Upload failed.",
        },
      }));
    }
  }, [uploads, ingestPlatform, ingestBank]);

  return (
    <div className="space-y-8 animate-fade-in">
      <section className="overflow-hidden rounded-2xl border border-blue-500/15 bg-gradient-to-br from-blue-500/[0.08] via-[#0c1018] to-canvas px-6 py-8">
        <div className="flex flex-col gap-6 lg:flex-row lg:items-end lg:justify-between">
          <div>
            <div className="inline-flex items-center gap-2 rounded-full border border-blue-500/25 bg-blue-500/10 px-3 py-1 text-[11px] font-medium uppercase tracking-widest text-blue-400">
              <Upload className="h-3 w-3" />
              Data ingestion
            </div>
            <h1 className="mt-4 text-3xl font-semibold tracking-tight sm:text-4xl">
              Upload Center
            </h1>
            <p className="mt-2 max-w-xl text-sm text-muted sm:text-base">
              Ingest platform and bank settlement files separately. Files are validated, hashed,
              and processed in the background while you continue working.
            </p>
          </div>
          <button
            type="button"
            onClick={() => createRun.mutate({})}
            disabled={createRun.isPending}
            className="inline-flex h-10 shrink-0 items-center justify-center gap-2 rounded-md border border-accent/30 bg-accent px-4 text-sm font-medium text-white shadow-glow transition-colors hover:bg-accent-hover disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {createRun.isPending ? <Loader2 className="h-4 w-4 animate-spin" /> : <Play className="h-4 w-4" />}
            Start reconciliation run
          </button>
        </div>
      </section>

      <section className="grid gap-8 lg:grid-cols-[280px_1fr]">
        <aside className="space-y-1">
          <p className="mb-4 text-[11px] font-medium uppercase tracking-widest text-muted">
            Ingestion pipeline
          </p>
          {steps.map((step) => (
            <div
              key={step.num}
              className="relative flex gap-4 rounded-xl border border-border/60 bg-surface/50 p-4"
            >
              <div className="flex h-9 w-9 shrink-0 items-center justify-center rounded-lg bg-accent/10 text-accent">
                <step.icon className="h-4 w-4" />
              </div>
              <div>
                <p className="font-mono text-[10px] text-blue-400/80">{step.num}</p>
                <p className="text-sm font-medium">{step.title}</p>
                <p className="mt-1 text-xs leading-relaxed text-muted">{step.desc}</p>
              </div>
            </div>
          ))}

          <div className="mt-6 space-y-3 rounded-xl border border-border bg-surface/30 p-4">
            <p className="text-xs font-medium uppercase tracking-wider text-muted">
              Upload controls
            </p>
            <div className="flex items-center gap-2 text-xs text-muted">
              <Database className="h-3.5 w-3.5 text-blue-400" />
              CSV, JSONL, and NDJSON
            </div>
            <div className="flex items-center gap-2 text-xs text-muted">
              <Hash className="h-3.5 w-3.5 text-blue-400" />
              SHA-256 deduplication
            </div>
            <div className="flex items-center gap-2 text-xs text-muted">
              <Shield className="h-3.5 w-3.5 text-blue-400" />
              Immutable audit on upload
            </div>
          </div>
        </aside>

        <div className="space-y-6">
          <div className="grid gap-6 md:grid-cols-2">
            <UploadCard
              kind="platform"
              title="Platform file"
              subtitle="Merchant transaction ledger"
              description="platform CSV / JSONL"
              icon={Building2}
              state={uploads.platform}
              onSelect={selectFile}
              onUpload={runUpload}
            />
            <UploadCard
              kind="bank"
              title="Bank settlement file"
              subtitle="Acquirer / bank settlement batch"
              description="bank CSV / JSONL"
              icon={Landmark}
              state={uploads.bank}
              onSelect={selectFile}
              onUpload={runUpload}
            />
          </div>

          <div className="grid gap-6 lg:grid-cols-2">
            <SampleFileList title="Platform sample files" files={sampleFiles.platform} />
            <SampleFileList title="Bank sample files" files={sampleFiles.bank} />
          </div>

          <div className="flex flex-col gap-4 rounded-2xl border border-border bg-surface-elevated/50 px-6 py-5 sm:flex-row sm:items-center sm:justify-between">
            <div className="flex items-start gap-3">
              <CheckCircle2 className="mt-0.5 h-5 w-5 shrink-0 text-blue-400" />
              <div>
                <p className="text-sm font-medium">Files uploaded?</p>
                <p className="mt-0.5 text-xs text-muted">
                  Head to the dashboard to monitor runs or start reconciliation.
                </p>
              </div>
            </div>
            <Link
              to="/dashboard"
              className="inline-flex h-9 items-center justify-center rounded-md border border-border px-4 text-sm font-medium text-foreground transition-colors hover:bg-surface-hover"
            >
              Dashboard
            </Link>
          </div>
        </div>
      </section>
    </div>
  );
}

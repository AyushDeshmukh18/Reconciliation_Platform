export type GapType =
  | "timing_gap"
  | "rounding_difference"
  | "duplicate_entry"
  | "orphan_refund"
  | "partial_settlement"
  | "failed_reversal"
  | "split_settlement"
  | "stale_retry"
  | "settlement_truncation"
  | "status_mismatch"
  | "idempotency_failure"
  | "unclassified";

export type ReconStatus =
  | "unprocessed"
  | "matched"
  | "partially_matched"
  | "flagged"
  | "manually_resolved"
  | "closed";

export type MatchType = "exact" | "fuzzy" | "composite" | "partial" | "unmatched";

export type RunStatus = "queued" | "running" | "completed" | "failed";

export type UserRole = "admin" | "analyst";

export interface User {
  user_id: string;
  username: string;
  email: string;
  role: UserRole;
}

export interface TokenResponse {
  access_token: string;
  refresh_token: string;
  token_type: string;
}

export interface LoginRequest {
  username: string;
  password: string;
}

export interface GapTypeSummary {
  count: number;
  monetary_exposure_minor_units: number;
  percentage: number;
}

export interface ReconciliationRun {
  run_id: string;
  triggered_by: string;
  started_at_utc: string;
  completed_at_utc: string | null;
  status: RunStatus;
  total_records: number;
  matched_count: number;
  unmatched_count: number;
  partially_matched_count: number;
  flagged_count: number;
  total_monetary_exposure_minor_units: number;
  celery_task_id: string | null;
  error_message: string | null;
  idempotency_key: string;
  date_range_start: string | null;
  date_range_end: string | null;
  progress_percent: number;
  progress_message: string | null;
  gap_type_breakdown: Record<string, GapTypeSummary>;
}

export interface ReconciliationRunCreate {
  idempotency_key: string;
  date_range_start?: string;
  date_range_end?: string;
}

export interface IngestResponse {
  task_id: string;
  file_hash: string;
  status: string;
  record_count_estimated: number;
  accepted?: number;
  rejected?: number;
}

export interface JobProgress {
  task_id: string;
  status: string;
  progress_percent: number;
  message: string;
  eta_seconds: number | null;
}

export interface ExceptionListItem {
  result_id: string;
  run_id: string;
  gap_type: GapType;
  gap_confidence: number;
  recon_status: ReconStatus;
  monetary_difference_minor_units: number;
  platform_transaction_id: string | null;
  bank_settlement_id: string | null;
  created_at_utc: string;
  merchant_id: string | null;
  requires_secondary_review: boolean;
}

export interface PlatformTransaction {
  transaction_id: string;
  merchant_id: string;
  amount_minor_units: number;
  currency_code: string;
  transaction_status: string;
  created_at_utc: string;
  idempotency_key: string | null;
  parent_transaction_id: string | null;
  source_file_hash?: string;
}

export interface BankSettlement {
  settlement_id: string;
  batch_id: string;
  transaction_reference: string;
  settled_amount_minor_units: number;
  fee_amount_minor_units: number;
  net_settled_amount_minor_units: number;
  value_date_utc: string;
  processing_date_utc: string;
  settlement_status: string;
  file_hash: string;
  batch_sequence_number?: number;
}

export interface ResolutionNote {
  note_id: string;
  analyst_id: string;
  note_text: string;
  is_ai_suggested: boolean;
  created_at_utc: string;
}

export interface RuleEvaluation {
  rule_id: string;
  gap_type: string;
  conditions_tested: Record<string, boolean | unknown>;
  fired: boolean;
  confidence: number | null;
}

export interface ExceptionDetail extends ExceptionListItem {
  platform_transaction: PlatformTransaction | null;
  bank_settlement: BankSettlement | null;
  rule_evaluation_trace: RuleEvaluation[] | Record<string, unknown>[];
  gap_explanation: string | null;
  resolution_suggestion: string | null;
  resolution_notes: ResolutionNote[];
}

export interface StatusUpdateRequest {
  new_status: ReconStatus;
  note?: string;
}

export interface BulkResolveRequest {
  result_ids: string[];
  note_text: string;
  confirmation: boolean;
}

export interface ResolutionNoteCreate {
  note_text: string;
  accept_ai_suggestion?: boolean;
}

export interface ExceptionFilters {
  gap_type?: GapType;
  recon_status?: ReconStatus;
  merchant_id?: string;
  amount_min?: number;
  amount_max?: number;
  run_id?: string;
  page?: number;
  page_size?: number;
}

export interface AuditLogEntry {
  event_id: string;
  event_type: string;
  entity_id: string;
  entity_type: string;
  actor: string;
  before_state: Record<string, unknown> | null;
  after_state: Record<string, unknown> | null;
  created_at_utc: string;
  correlation_id: string;
  file_hash: string | null;
}

export interface ReportMeta {
  report_id: string;
  run_id: string;
  format: string;
  generated_at: string;
  requested_by: string;
  pdf_path: string | null;
  csv_path: string | null;
  exception_count: number;
}

export interface ReportGenerateRequest {
  run_id: string;
  format: "pdf" | "csv";
}

export interface ApiError {
  error_code: string;
  message: string;
  correlation_id: string;
  docs_url: string;
}

export const GAP_TYPE_LABELS: Record<GapType, string> = {
  timing_gap: "Timing Gap",
  rounding_difference: "Rounding",
  duplicate_entry: "Duplicate",
  orphan_refund: "Orphan Refund",
  partial_settlement: "Partial Settlement",
  failed_reversal: "Failed Reversal",
  split_settlement: "Split Settlement",
  stale_retry: "Stale Retry",
  settlement_truncation: "Truncation",
  status_mismatch: "Status Mismatch",
  idempotency_failure: "Idempotency",
  unclassified: "Unclassified",
};

export const RECON_STATUS_LABELS: Record<ReconStatus, string> = {
  unprocessed: "Unprocessed",
  matched: "Matched",
  partially_matched: "Partial",
  flagged: "Flagged",
  manually_resolved: "Resolved",
  closed: "Closed",
};

export const VALID_TRANSITIONS: Partial<Record<ReconStatus, ReconStatus[]>> = {
  flagged: ["manually_resolved"],
  manually_resolved: ["closed"],
  matched: ["closed"],
};

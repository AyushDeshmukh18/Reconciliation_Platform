import calendar
from dataclasses import dataclass
from datetime import timedelta

from backend.engine.tolerance import compute_tolerance_band
from backend.rules.confidence import GapClassification, compute_confidence


def classify_timing_gap(unmatched_platform_record, run_date_range=None):
    created = unmatched_platform_record["created_at_utc"]
    last_day = calendar.monthrange(created.year, created.month)[1]
    days_from_end = last_day - created.day
    if days_from_end > 2:
        return None
    confidence = 95.0 if days_from_end <= 1 else 70.0
    return GapClassification(
        gap_type="timing_gap",
        confidence=confidence,
        rule_id="TIMING_GAP_001",
        recommended_action="Track as open receivable; expect settlement in next month batch",
        requires_secondary_review=confidence < 70,
        trace=[{"condition": "last_days_of_month", "passed": True}],
    )


def classify_rounding_difference(platform_record, bank_record):
    p_amt = int(platform_record["amount_minor_units"])
    b_amt = int(bank_record["net_settled_amount_minor_units"])
    diff = p_amt - b_amt
    tol = compute_tolerance_band(p_amt)
    if diff == 0 or abs(diff) > tol:
        return None
    floor_pattern = (p_amt // 100) * 100 - b_amt
    if abs(diff - floor_pattern) <= 1 or abs(diff) <= 1:
        return GapClassification(
            gap_type="rounding_difference",
            confidence=90.0,
            rule_id="ROUNDING_DIFFERENCE_001",
            recommended_action="Accept rounding variance within tolerance band",
            requires_secondary_review=False,
            trace=[{"condition": "within_tolerance", "passed": True}],
        )
    return None


def classify_duplicate_entry(records_group):
    if len(records_group) < 2:
        return None
    ids = [str(r.get("transaction_id")) for r in records_group]
    same_id = len(set(ids)) < len(ids)
    confidence = 99.0 if same_id else 85.0
    return GapClassification(
        gap_type="duplicate_entry",
        confidence=confidence,
        rule_id="DUPLICATE_ENTRY_001",
        recommended_action="Identify which entry is authoritative; void the duplicate",
        requires_secondary_review=False,
        trace=[{"condition": "duplicate_pattern", "passed": True}],
    )


def classify_orphan_refund(platform_record, context=None):
    status = str(platform_record.get("transaction_status", "")).lower()
    if status not in ("reversed", "voided"):
        return None
    parent = platform_record.get("parent_transaction_id")
    parent_exists = context and context.get("parent_exists", False) if context else False
    if parent and parent_exists:
        return None
    return GapClassification(
        gap_type="orphan_refund",
        confidence=95.0,
        rule_id="ORPHAN_REFUND_001",
        recommended_action="Locate original transaction or initiate manual refund trace",
        requires_secondary_review=False,
        trace=[{"condition": "orphan_refund", "passed": True}],
    )


def classify_partial_settlement(platform_record, bank_record):
    p_amt = int(platform_record["amount_minor_units"])
    b_amt = int(bank_record["net_settled_amount_minor_units"])
    tol = compute_tolerance_band(p_amt)
    if b_amt <= 0 or b_amt >= p_amt - tol:
        return None
    ratio = b_amt / p_amt if p_amt else 0
    if 0.6 <= ratio <= 0.99:
        return GapClassification(
            gap_type="partial_settlement",
            confidence=92.0,
            rule_id="PARTIAL_SETTLEMENT_001",
            recommended_action="Track remaining amount as open receivable",
            requires_secondary_review=False,
            trace=[{"condition": "partial_ratio", "passed": True, "ratio": ratio}],
        )
    return None


def classify_failed_reversal(platform_record, bank_record):
    ps = str(platform_record.get("transaction_status", "")).lower()
    bs = str(bank_record.get("settlement_status", "")).lower()
    if ps in ("reversed", "voided") and bs == "settled":
        return GapClassification(
            gap_type="failed_reversal",
            confidence=98.0,
            rule_id="FAILED_REVERSAL_001",
            recommended_action="URGENT: Initiate bank recall. Compliance exposure if within chargeback window.",
            requires_secondary_review=True,
            trace=[{"condition": "failed_reversal", "passed": True}],
        )
    return None


def classify_split_settlement(platform_record, bank_records_group):
    p_amt = int(platform_record["amount_minor_units"])
    total = sum(int(b["net_settled_amount_minor_units"]) for b in bank_records_group)
    tol = compute_tolerance_band(p_amt)
    if abs(total - p_amt) > tol:
        return None
    batches = {b.get("batch_id") for b in bank_records_group}
    dates = {b.get("value_date_utc") for b in bank_records_group}
    if len(batches) <= 1 and len(dates) <= 1:
        return None
    confidence = 90.0 if total == p_amt else 75.0
    return GapClassification(
        gap_type="split_settlement",
        confidence=confidence,
        rule_id="SPLIT_SETTLEMENT_001",
        recommended_action="Verify split settlement batches sum to platform amount",
        requires_secondary_review=confidence < 70,
        trace=[{"condition": "split_sum", "passed": True}],
    )


def classify_stale_retry(platform_record, bank_records):
    ref = str(platform_record.get("transaction_id", ""))
    matching = [b for b in bank_records if str(b.get("transaction_reference")) == ref]
    if len(matching) < 2:
        return None
    matching.sort(key=lambda x: x["value_date_utc"])
    delta = (matching[-1]["value_date_utc"] - matching[0]["value_date_utc"]).days
    if 3 <= delta <= 5:
        return GapClassification(
            gap_type="stale_retry",
            confidence=88.0,
            rule_id="STALE_RETRY_001",
            recommended_action="Verify with bank: second settlement may be unauthorized re-presentation",
            requires_secondary_review=False,
            trace=[{"condition": "stale_retry_days", "passed": True, "days": delta}],
        )
    return None


def classify_settlement_truncation(platform_records, bank_records, batch_level=True):
    p_sum = sum(int(p["amount_minor_units"]) for p in platform_records)
    b_sum = sum(int(b["net_settled_amount_minor_units"]) for b in bank_records)
    diff = p_sum - b_sum
    if diff <= 0:
        return None
    expected = len(platform_records) * 0.5
    if abs(diff - expected * 100) <= len(platform_records) * 50:
        return GapClassification(
            gap_type="settlement_truncation",
            confidence=85.0,
            rule_id="SETTLEMENT_TRUNCATION_001",
            recommended_action="Review batch-level floor rounding truncation",
            requires_secondary_review=False,
            trace=[{"condition": "batch_truncation", "passed": True}],
        )
    return None


def classify_status_mismatch(platform_record, bank_record):
    p_amt = int(platform_record["amount_minor_units"])
    b_amt = int(bank_record["net_settled_amount_minor_units"])
    tol = compute_tolerance_band(p_amt)
    if abs(p_amt - b_amt) > tol:
        return None
    ps = str(platform_record.get("transaction_status", "")).lower()
    bs = str(bank_record.get("settlement_status", "")).lower()
    mismatch = (ps == "success" and bs in ("reversed", "returned")) or (
        ps in ("reversed", "voided") and bs == "settled"
    )
    if mismatch:
        return GapClassification(
            gap_type="status_mismatch",
            confidence=99.0,
            rule_id="STATUS_MISMATCH_001",
            recommended_action="Investigate status divergence immediately",
            requires_secondary_review=False,
            trace=[{"condition": "status_mismatch", "passed": True}],
        )
    return None


def classify_idempotency_failure(platform_record, bank_records):
    key = platform_record.get("idempotency_key")
    if not key:
        return None
    matching = [b for b in bank_records if b.get("raw_record", {}).get("idempotency_key") == key]
    if len(matching) >= 2:
        return GapClassification(
            gap_type="idempotency_failure",
            confidence=92.0,
            rule_id="IDEMPOTENCY_FAILURE_001",
            recommended_action="Recall second settlement from bank. Do not void platform record.",
            requires_secondary_review=False,
            trace=[{"condition": "duplicate_bank_idempotency", "passed": True}],
        )
    return None

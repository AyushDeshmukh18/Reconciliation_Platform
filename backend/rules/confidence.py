from dataclasses import dataclass
from datetime import timedelta


@dataclass
class GapClassification:
    gap_type: str
    confidence: float
    rule_id: str | None
    recommended_action: str
    requires_secondary_review: bool
    trace: list[dict]


def compute_confidence(gap_type: str, matching_fields: dict, context: dict) -> float:
    base_map = {
        "timing_gap": 70.0,
        "rounding_difference": 90.0,
        "duplicate_entry": 85.0,
        "orphan_refund": 95.0,
        "partial_settlement": 92.0,
        "failed_reversal": 98.0,
        "split_settlement": 75.0,
        "stale_retry": 88.0,
        "settlement_truncation": 85.0,
        "status_mismatch": 99.0,
        "idempotency_failure": 92.0,
        "unclassified": 50.0,
    }
    confidence = base_map.get(gap_type, 60.0)
    corroborating = sum(1 for v in matching_fields.values() if v)
    confidence += min(corroborating * 2.5, 10.0)
    if context.get("conflicting_signals"):
        confidence -= 15.0
    return max(0.0, min(100.0, confidence))

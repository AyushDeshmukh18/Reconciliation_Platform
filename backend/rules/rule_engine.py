from backend.rules import gap_classifiers
from backend.rules.confidence import GapClassification, compute_confidence


class RuleEngine:
    CLASSIFIERS = [
        ("failed_reversal", gap_classifiers.classify_failed_reversal),
        ("status_mismatch", gap_classifiers.classify_status_mismatch),
        ("partial_settlement", gap_classifiers.classify_partial_settlement),
        ("rounding_difference", gap_classifiers.classify_rounding_difference),
        ("orphan_refund", gap_classifiers.classify_orphan_refund),
        ("timing_gap", gap_classifiers.classify_timing_gap),
        ("stale_retry", gap_classifiers.classify_stale_retry),
        ("idempotency_failure", gap_classifiers.classify_idempotency_failure),
        ("duplicate_entry", gap_classifiers.classify_duplicate_entry),
        ("split_settlement", gap_classifiers.classify_split_settlement),
    ]

    def __init__(self, rules_from_db: list | None = None):
        self.rules = rules_from_db or []

    def evaluate(self, platform_record, bank_record, context=None) -> GapClassification:
        context = context or {}
        trace: list[dict] = []

        if platform_record and bank_record:
            for name, fn in self.CLASSIFIERS:
                if name in ("timing_gap", "orphan_refund", "duplicate_entry"):
                    continue
                try:
                    result = fn(platform_record, bank_record)
                except TypeError:
                    continue
                trace.append({"rule": name, "fired": result is not None})
                if result:
                    result.trace = trace
                    if result.confidence < 70:
                        result.requires_secondary_review = True
                    return result

        if platform_record and not bank_record:
            result = gap_classifiers.classify_timing_gap(platform_record, context.get("run_date_range"))
            trace.append({"rule": "timing_gap", "fired": result is not None})
            if result:
                result.trace = trace
                return result
            result = gap_classifiers.classify_orphan_refund(
                platform_record, {"parent_exists": context.get("parent_exists", False)}
            )
            trace.append({"rule": "orphan_refund", "fired": result is not None})
            if result:
                result.trace = trace
                return result

        if bank_record and not platform_record:
            trace.append({"rule": "unmatched_bank", "fired": True})

        confidence = compute_confidence("unclassified", {}, context)
        return GapClassification(
            gap_type="unclassified",
            confidence=confidence,
            rule_id=None,
            recommended_action="Escalate for manual classification",
            requires_secondary_review=True,
            trace=trace,
        )

    def dry_run(self, record_dict: dict) -> dict:
        platform = record_dict.get("platform") or record_dict
        bank = record_dict.get("bank")
        trace = []
        winning = None
        gap_type = None
        confidence = 0.0

        for name, fn in self.CLASSIFIERS:
            fired = False
            conf = None
            try:
                if bank is not None:
                    result = fn(platform, bank)
                elif name == "timing_gap":
                    result = fn(platform)
                elif name == "orphan_refund":
                    result = fn(platform, {})
                else:
                    result = None
                if result:
                    fired = True
                    conf = result.confidence
                    if not winning:
                        winning = result.rule_id
                        gap_type = result.gap_type
                        confidence = result.confidence
            except TypeError:
                result = None
            trace.append(
                {
                    "rule_id": name.upper() + "_001",
                    "gap_type": name,
                    "conditions_tested": {"evaluated": True},
                    "fired": fired,
                    "confidence": conf,
                }
            )

        if not winning:
            gap_type = "unclassified"
            confidence = 50.0

        return {
            "rules_evaluated": trace,
            "winning_rule": winning,
            "gap_type": gap_type,
            "confidence": confidence,
        }

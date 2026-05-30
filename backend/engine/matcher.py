from dataclasses import dataclass
from datetime import timedelta

from backend.engine.tolerance import compute_tolerance_band


@dataclass
class MatchPair:
    platform: dict
    bank: dict | list[dict]
    match_type: str
    confidence: float
    gap_type: str | None = None
    monetary_difference: int = 0


class ReconciliationMatcher:
    def _platform_amount(self, p: dict) -> int:
        return int(p["amount_minor_units"])

    def _bank_net(self, b: dict) -> int:
        return int(b["net_settled_amount_minor_units"])

    def _status_mismatch(self, platform: dict, bank: dict) -> bool:
        ps = str(platform.get("transaction_status", "")).lower()
        bs = str(bank.get("settlement_status", "")).lower()
        if ps == "success" and bs in ("reversed", "returned"):
            return True
        if ps in ("reversed", "voided") and bs == "settled":
            return True
        return False

    async def pass_1_exact_match(self, platform_records, bank_records):
        bank_by_ref = {}
        for b in bank_records:
            bank_by_ref.setdefault(str(b["transaction_reference"]), []).append(b)

        matched_pairs: list[MatchPair] = []
        unmatched_platform = []
        matched_bank_ids = set()

        for p in platform_records:
            ref = str(p.get("transaction_id", ""))
            candidates = bank_by_ref.get(ref, [])
            found = None
            for b in candidates:
                if b["settlement_id"] in matched_bank_ids:
                    continue
                diff = self._platform_amount(p) - self._bank_net(b)
                tol = compute_tolerance_band(self._platform_amount(p))
                if abs(diff) <= tol:
                    found = b
                    gap = "status_mismatch" if self._status_mismatch(p, b) else None
                    matched_pairs.append(
                        MatchPair(
                            platform=p,
                            bank=b,
                            match_type="exact",
                            confidence=99.0 if not gap else 99.0,
                            gap_type=gap,
                            monetary_difference=diff,
                        )
                    )
                    matched_bank_ids.add(b["settlement_id"])
                    break
            if not found:
                unmatched_platform.append(p)

        unmatched_bank = [b for b in bank_records if b["settlement_id"] not in matched_bank_ids]
        return matched_pairs, unmatched_platform, unmatched_bank

    async def pass_2_fuzzy_match(self, unmatched_platform, unmatched_bank):
        fuzzy_matches: list[MatchPair] = []
        matched_bank_ids = set()
        still_unmatched_platform = []

        from collections import defaultdict
        # Pre-index bank records for faster lookups
        bank_by_merchant: dict[str | None, list[dict]] = defaultdict(list)
        bank_list = list(unmatched_bank)
        for b in bank_list:
            bank_by_merchant[b.get("merchant_id")].append(b)
        bank_by_merchant[None] = bank_list

        for p in unmatched_platform:
            p_amt = self._platform_amount(p)
            p_date = p["created_at_utc"]
            p_merchant = p.get("merchant_id")
            # Get candidates first: same merchant, or all
            candidates = bank_by_merchant.get(p_merchant, [])
            if not candidates:
                candidates = bank_list
            best = None
            best_diff = None
            for b in candidates:
                if b["settlement_id"] in matched_bank_ids:
                    continue
                if p_merchant and b.get("merchant_id") and p_merchant != b.get("merchant_id"):
                    if str(b.get("transaction_reference", ""))[:8] != str(p_merchant)[:8]:
                        continue
                diff = p_amt - self._bank_net(b)
                tol = compute_tolerance_band(p_amt)
                if abs(diff) > tol:
                    continue
                b_date = b["value_date_utc"]
                if abs((p_date - b_date).days) > 2:
                    continue
                if best is None or abs(diff) < abs(best_diff):
                    best = b
                    best_diff = diff
            if best:
                fuzzy_matches.append(
                    MatchPair(
                        platform=p,
                        bank=best,
                        match_type="fuzzy",
                        confidence=82.0,
                        monetary_difference=best_diff or 0,
                    )
                )
                matched_bank_ids.add(best["settlement_id"])
            else:
                still_unmatched_platform.append(p)

        still_unmatched_bank = [b for b in unmatched_bank if b["settlement_id"] not in matched_bank_ids]
        return fuzzy_matches, still_unmatched_platform, still_unmatched_bank

    async def pass_3_composite_match(self, unmatched_platform, unmatched_bank):
        composite_matches: list[MatchPair] = []
        matched_platform_ids = set()
        matched_bank_ids = set()
        duplicates: list[MatchPair] = []

        from collections import defaultdict

        platform_groups: dict[tuple, list] = defaultdict(list)
        for p in unmatched_platform:
            key = (p.get("merchant_id"), self._platform_amount(p))
            ts = p["created_at_utc"]
            platform_groups[key].append(p)

        for key, group in platform_groups.items():
            if len(group) < 2:
                continue
            group.sort(key=lambda x: x["created_at_utc"])
            for i in range(len(group) - 1):
                delta = (group[i + 1]["created_at_utc"] - group[i]["created_at_utc"]).total_seconds()
                if delta <= 60:
                    duplicates.append(
                        MatchPair(
                            platform=group[i + 1],
                            bank=[],
                            match_type="unmatched",
                            confidence=99.0,
                            gap_type="duplicate_entry",
                            monetary_difference=0,
                        )
                    )
                    matched_platform_ids.add(group[i + 1]["transaction_id"])

        bank_by_ref: dict[str, list] = defaultdict(list)
        for b in unmatched_bank:
            bank_by_ref[str(b["transaction_reference"])].append(b)

        for ref, banks in bank_by_ref.items():
            if len(banks) >= 2:
                banks.sort(key=lambda x: x["value_date_utc"])
                delta_days = (banks[-1]["value_date_utc"] - banks[0]["value_date_utc"]).days
                if 3 <= delta_days <= 5:
                    for b in banks[1:]:
                        duplicates.append(
                            MatchPair(
                                platform={"transaction_id": ref},
                                bank=b,
                                match_type="unmatched",
                                confidence=88.0,
                                gap_type="stale_retry",
                                monetary_difference=0,
                            )
                        )
                        matched_bank_ids.add(b["settlement_id"])

        # Pre-index bank by batch
        by_batch: dict[str, list] = defaultdict(list)
        for b in unmatched_bank:
            if b["settlement_id"] not in matched_bank_ids:
                by_batch[b["batch_id"]].append(b)
                
        for p in unmatched_platform:
            if p["transaction_id"] in matched_platform_ids:
                continue
            p_amt = self._platform_amount(p)
            tol = compute_tolerance_band(p_amt)
            ref = str(p["transaction_id"])
            
            # Check each batch
            for batch_id, batch_banks in by_batch.items():
                total = sum(self._bank_net(b) for b in batch_banks)
                if abs(total - p_amt) <= tol and len(batch_banks) > 1:
                    composite_matches.append(
                        MatchPair(
                            platform=p,
                            bank=batch_banks,
                            match_type="composite",
                            confidence=90.0,
                            gap_type="split_settlement",
                            monetary_difference=p_amt - total,
                        )
                    )
                    matched_platform_ids.add(p["transaction_id"])
                    for b in batch_banks:
                        matched_bank_ids.add(b["settlement_id"])
                    break

        residuals_platform = [p for p in unmatched_platform if p["transaction_id"] not in matched_platform_ids]
        residuals_bank = [b for b in unmatched_bank if b["settlement_id"] not in matched_bank_ids]
        return composite_matches + duplicates, (residuals_platform, residuals_bank)

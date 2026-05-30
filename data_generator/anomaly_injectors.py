import copy
import random
import uuid
from datetime import timedelta


def inject_timing_gap(rng, platform_records, bank_records, transaction_count=1):
    if not platform_records:
        return None
    p = rng.choice(platform_records)
    p["timestamp"] = p.get("created_at_utc", p.get("timestamp"))
    return {"gap_type": "timing_gap", "transaction_id": p["transaction_id"]}


def inject_rounding_difference(rng, platform_records, bank_records, rate=0.02):
    if not platform_records or not bank_records:
        return None
    p = rng.choice(platform_records)
    for b in bank_records:
        if str(b.get("transaction_reference")) == str(p.get("transaction_id")):
            b["settled_amount"] = round(float(p.get("amount", 0)) - 0.005, 3)
            return {"gap_type": "rounding_difference", "transaction_id": p["transaction_id"]}
    return None


def inject_duplicate_entry(rng, platform_records, bank_records, rate=0.003):
    if not platform_records:
        return None
    src = rng.choice(platform_records)
    dup = copy.deepcopy(src)
    dup["transaction_id"] = str(uuid.uuid4())
    offset = rng.randint(0, 300)
    platform_records.append(dup)
    return {"gap_type": "duplicate_entry", "transaction_id": dup["transaction_id"]}


def inject_orphan_refund(rng, platform_records, rate=0.004):
    tid = str(uuid.uuid4())
    platform_records.append(
        {
            "transaction_id": tid,
            "merchant_id": f"MERCHANT_{rng.randint(1, 100):03d}",
            "amount": round(rng.uniform(100, 5000), 2),
            "status": "reversed",
            "timestamp": datetime.now().isoformat(),
            "parent_transaction_id": str(uuid.uuid4()),
        }
    )
    return {"gap_type": "orphan_refund", "transaction_id": tid}


from datetime import datetime  # noqa: E402


def inject_partial_settlement(rng, platform_records, bank_records, rate=0.008):
    if not platform_records or not bank_records:
        return None
    p = rng.choice(platform_records)
    for b in bank_records:
        if str(b.get("transaction_reference")) == str(p.get("transaction_id")):
            ratio = rng.uniform(0.6, 0.95)
            amt = float(p.get("amount", 1000))
            b["settled_amount"] = round(amt * ratio, 2)
            b["net_settled_amount_minor_units"] = int(amt * ratio * 100)
            return {"gap_type": "partial_settlement", "transaction_id": p["transaction_id"]}
    return None


def inject_failed_reversal(rng, platform_records, bank_records, rate=0.003):
    if not platform_records:
        return None
    p = rng.choice(platform_records)
    p["status"] = "reversed"
    return {"gap_type": "failed_reversal", "transaction_id": p["transaction_id"]}


def inject_split_settlement(rng, platform_records, bank_records, rate=0.006):
    if not platform_records or not bank_records:
        return None
    p = rng.choice(platform_records)
    matching = [b for b in bank_records if str(b.get("transaction_reference")) == str(p.get("transaction_id"))]
    if not matching:
        return None
    original = matching[0]
    bank_records.remove(original)
    amt = float(original.get("settled_amount", p.get("amount", 100)))
    part1 = round(amt * 0.6, 2)
    part2 = round(amt - part1, 2)
    for i, part in enumerate([part1, part2]):
        bank_records.append(
            {
                **original,
                "settlement_id": str(uuid.uuid4()),
                "settled_amount": part,
                "batch_id": f"{original.get('batch_id')}_S{i}",
            }
        )
    return {"gap_type": "split_settlement", "transaction_id": p["transaction_id"]}


def inject_stale_retry(rng, bank_records, rate=0.004):
    if not bank_records:
        return None
    b = rng.choice(bank_records)
    retry = copy.deepcopy(b)
    retry["settlement_id"] = str(uuid.uuid4())
    vd = b.get("value_date_utc") or b.get("value_date")
    if isinstance(vd, str):
        from dateutil import parser

        vd = parser.isoparse(vd)
    retry["value_date"] = (vd + timedelta(days=rng.randint(3, 5))).isoformat()
    bank_records.append(retry)
    return {"gap_type": "stale_retry", "transaction_id": b.get("transaction_reference")}


def inject_settlement_truncation(rng, bank_records, rate=0.01):
    if len(bank_records) < 10:
        return None
    batch = rng.choice(bank_records).get("batch_id")
    for b in bank_records:
        if b.get("batch_id") == batch:
            amt = float(b.get("settled_amount", 100))
            b["settled_amount"] = math.floor(amt * 100) / 100
    return {"gap_type": "settlement_truncation", "batch_id": batch}


import math  # noqa: E402


def inject_status_mismatch(rng, platform_records, bank_records, rate=0.005):
    if not platform_records or not bank_records:
        return None
    p = rng.choice(platform_records)
    p["status"] = "success"
    for b in bank_records:
        if str(b.get("transaction_reference")) == str(p.get("transaction_id")):
            b["settlement_status"] = "reversed"
            return {"gap_type": "status_mismatch", "transaction_id": p["transaction_id"]}
    return None


def inject_idempotency_failure(rng, platform_records, bank_records, rate=0.002):
    if not platform_records or not bank_records:
        return None
    p = rng.choice(platform_records)
    key = p.get("idempotency_key") or str(uuid.uuid4())
    p["idempotency_key"] = key
    for b in bank_records:
        if str(b.get("transaction_reference")) == str(p.get("transaction_id")):
            dup = copy.deepcopy(b)
            dup["settlement_id"] = str(uuid.uuid4())
            dup["idempotency_key"] = key
            bank_records.append(dup)
            return {"gap_type": "idempotency_failure", "transaction_id": p["transaction_id"]}
    return None

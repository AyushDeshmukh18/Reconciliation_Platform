import argparse
import calendar
import csv
import random
import uuid
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Literal

import pytz

from data_generator import anomaly_injectors as injectors
from data_generator.distributions import GeneratedDataset, sample_amount
from data_generator.manifest import write_manifest

IST = pytz.timezone("Asia/Kolkata")

ANOMALY_MAP = {
    "timing_gap": lambda rng, ds: injectors.inject_timing_gap(rng, ds.platform_records, ds.bank_records),
    "rounding_difference": lambda rng, ds: injectors.inject_rounding_difference(rng, ds.platform_records, ds.bank_records),
    "duplicate_entry": lambda rng, ds: injectors.inject_duplicate_entry(rng, ds.platform_records, ds.bank_records),
    "orphan_refund": lambda rng, ds: injectors.inject_orphan_refund(rng, ds.platform_records),
    "partial_settlement": lambda rng, ds: injectors.inject_partial_settlement(rng, ds.platform_records, ds.bank_records),
    "failed_reversal": lambda rng, ds: injectors.inject_failed_reversal(rng, ds.platform_records, ds.bank_records),
    "split_settlement": lambda rng, ds: injectors.inject_split_settlement(rng, ds.platform_records, ds.bank_records),
    "stale_retry": lambda rng, ds: injectors.inject_stale_retry(rng, ds.bank_records),
    "settlement_truncation": lambda rng, ds: injectors.inject_settlement_truncation(rng, ds.bank_records),
    "status_mismatch": lambda rng, ds: injectors.inject_status_mismatch(rng, ds.platform_records, ds.bank_records),
    "idempotency_failure": lambda rng, ds: injectors.inject_idempotency_failure(rng, ds.platform_records, ds.bank_records),
}


class DataGenerator:
    def __init__(self, seed: int, mode: Literal["scenario", "statistical"]):
        self.rng = random.Random(seed)
        self.seed = seed
        self.mode = mode

    def _random_timestamp(self, year: int, month: int) -> datetime:
        last_day = calendar.monthrange(year, month)[1]
        day = self.rng.randint(1, last_day)
        if day >= last_day - 1 and self.rng.random() < 0.3:
            day = self.rng.randint(max(1, last_day - 2), last_day)
        hour = self.rng.choice([10, 11, 14, 15, 16, self.rng.randint(8, 20)])
        dt = datetime(year, month, day, hour, self.rng.randint(0, 59), tzinfo=IST)
        if self.rng.random() < 0.05:
            dt = dt.astimezone(pytz.timezone("America/New_York"))
        return dt.astimezone(timezone.utc)

    def generate_month(
        self,
        year: int,
        month: int,
        transaction_count: int = 10_000,
        error_rates: dict | None = None,
    ) -> GeneratedDataset:
        dataset = GeneratedDataset()
        dataset.seed = self.seed

        for _ in range(transaction_count):
            amount = sample_amount(self.rng)
            tx_id = str(uuid.uuid4())
            merchant = f"MERCHANT_{self.rng.randint(1, 500):03d}"
            created = self._random_timestamp(year, month)
            settlement_delay = self.rng.choices([1, 2, 3], weights=[70, 25, 5])[0]
            value_date = created + timedelta(days=settlement_delay)
            idem_key = f"idk_{uuid.uuid4().hex[:12]}"

            platform = {
                "transaction_id": tx_id,
                "merchant_id": merchant,
                "amount": round(amount, 2),
                "amount_minor_units": int(round(amount * 100)),
                "currency_code": "INR",
                "status": "success",
                "timestamp": created.isoformat(),
                "idempotency_key": idem_key,
            }
            dataset.platform_records.append(platform)

            fee = round(amount * 0.003, 2)
            net = round(amount - fee, 2)
            bank = {
                "settlement_id": str(uuid.uuid4()),
                "batch_id": f"BATCH_{year}{month:02d}_{self.rng.randint(1, 50):03d}",
                "transaction_reference": tx_id,
                "settled_amount": round(amount, 2),
                "fee_amount": fee,
                "net_settled_amount_minor_units": int(round(net * 100)),
                "value_date": value_date.isoformat(),
                "processing_date": value_date.isoformat(),
                "settlement_status": "settled",
                "idempotency_key": idem_key,
            }
            dataset.bank_records.append(bank)

        if self.mode == "statistical" and error_rates:
            for gap_type, rate in error_rates.items():
                count = max(1, int(transaction_count * rate))
                for _ in range(count):
                    record = self.inject_anomaly(gap_type, dataset)
                    if record:
                        dataset.injected_anomalies.append(
                            {
                                **record,
                                "expected_classification": gap_type,
                                "expected_confidence_min": 70.0,
                                "injected_at": datetime.now(timezone.utc).isoformat(),
                            }
                        )
        elif self.mode == "scenario":
            for gap_type in ANOMALY_MAP:
                record = self.inject_anomaly(gap_type, dataset)
                if record:
                    dataset.injected_anomalies.append(
                        {
                            **record,
                            "expected_classification": gap_type,
                            "expected_confidence_min": 70.0,
                            "injected_at": datetime.now(timezone.utc).isoformat(),
                        }
                    )

        return dataset

    def inject_anomaly(self, gap_type: str, dataset: GeneratedDataset) -> dict | None:
        fn = ANOMALY_MAP.get(gap_type)
        if not fn:
            return None
        return fn(self.rng, dataset)


def _write_csv(records: list[dict], path: Path) -> None:
    if not records:
        return
    keys: set[str] = set()
    for r in records:
        keys.update(r.keys())
    fieldnames = sorted(keys)
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(records)


def main():
    parser = argparse.ArgumentParser(description="Generate reconciliation test data")
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--mode", choices=["scenario", "statistical"], default="statistical")
    parser.add_argument("--year", type=int, default=datetime.now().year)
    parser.add_argument("--month", type=int, default=datetime.now().month)
    parser.add_argument("--count", type=int, default=1000)
    parser.add_argument("--output", type=str, default="./test_data")
    args = parser.parse_args()

    gen = DataGenerator(args.seed, args.mode)
    error_rates = {
        "timing_gap": 0.002,
        "rounding_difference": 0.02,
        "duplicate_entry": 0.003,
        "orphan_refund": 0.004,
        "partial_settlement": 0.008,
        "failed_reversal": 0.003,
        "split_settlement": 0.006,
        "stale_retry": 0.004,
        "settlement_truncation": 0.01,
        "status_mismatch": 0.005,
        "idempotency_failure": 0.002,
    }
    dataset = gen.generate_month(args.year, args.month, args.count, error_rates if args.mode == "statistical" else None)

    out = Path(args.output)
    out.mkdir(parents=True, exist_ok=True)
    _write_csv(dataset.platform_records, out / "platform_transactions.csv")
    _write_csv(dataset.bank_records, out / "bank_settlements.csv")
    write_manifest(dataset, str(out / "manifest.json"))
    print(f"Generated {len(dataset.platform_records)} platform + {len(dataset.bank_records)} bank records -> {out}")


if __name__ == "__main__":
    main()

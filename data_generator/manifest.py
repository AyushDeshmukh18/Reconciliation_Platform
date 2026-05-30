import json
from dataclasses import asdict
from datetime import datetime, timezone

from data_generator.distributions import GeneratedDataset


def write_manifest(dataset: GeneratedDataset, output_path: str) -> None:
    manifest = {
        "seed": getattr(dataset, "seed", 0),
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "total_platform_records": len(dataset.platform_records),
        "total_bank_records": len(dataset.bank_records),
        "expected_matched": len(dataset.platform_records) - len(dataset.injected_anomalies),
        "injected_anomalies": dataset.injected_anomalies,
    }
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=2, default=str)

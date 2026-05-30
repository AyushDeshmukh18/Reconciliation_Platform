import json
import math
import random
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytz

IST = pytz.timezone("Asia/Kolkata")


@dataclass
class GeneratedDataset:
    platform_records: list[dict] = field(default_factory=list)
    bank_records: list[dict] = field(default_factory=list)
    injected_anomalies: list[dict] = field(default_factory=list)


def log_normal_amount(rng: random.Random, mu: float, sigma: float, lo: float, hi: float) -> float:
    while True:
        val = rng.lognormvariate(mu, sigma)
        if lo <= val <= hi:
            return val


def sample_amount(rng: random.Random) -> float:
    bucket = rng.random()
    if bucket < 0.05:
        return rng.uniform(10, 100)
    if bucket < 0.65:
        return log_normal_amount(rng, math.log(500), 0.8, 100, 5000)
    if bucket < 0.90:
        return log_normal_amount(rng, math.log(15000), 0.6, 5000, 50000)
    return log_normal_amount(rng, math.log(150000), 0.5, 50000, 500000)

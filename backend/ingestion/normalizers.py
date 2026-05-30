import re
from datetime import datetime, timezone
from decimal import ROUND_FLOOR, ROUND_HALF_UP, Decimal

import pytz
from dateutil import parser as date_parser


def normalize_timestamp(ts_str: str) -> datetime:
    dt = date_parser.isoparse(ts_str)
    if dt.tzinfo is None:
        dt = pytz.UTC.localize(dt)
    else:
        dt = dt.astimezone(pytz.UTC)
    return dt


def _clean_amount_string(amount: str | float | Decimal) -> Decimal:
    if isinstance(amount, (int, float)):
        return Decimal(str(amount))
    if isinstance(amount, Decimal):
        return amount
    cleaned = re.sub(r"[^\d.\-]", "", str(amount).replace(",", ""))
    return Decimal(cleaned) if cleaned else Decimal("0")


def amount_to_minor_units(amount: str | float | Decimal, *, bank_floor: bool = False) -> int:
    dec = _clean_amount_string(amount)
    if bank_floor:
        minor = (dec * 100).quantize(Decimal("1"), rounding=ROUND_FLOOR)
    else:
        minor = (dec * 100).quantize(Decimal("1"), rounding=ROUND_HALF_UP)
    return int(minor)


def utc_now() -> datetime:
    return datetime.now(timezone.utc)

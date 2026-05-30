def compute_tolerance_band(amount_minor_units: int) -> int:
    """Return max allowed difference in minor units (paise)."""
    amount = abs(amount_minor_units)
    if amount < 100_000:
        return 50
    if amount <= 10_000_000:
        return max(1, int(amount * 0.0005))
    return 5_000

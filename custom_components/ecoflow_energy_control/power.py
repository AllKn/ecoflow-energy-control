"""Power value normalization helpers."""

from __future__ import annotations

from typing import Any


def normalize_powerstream_watts(value: float | None, max_watts: float) -> float:
    """Normalize EcoFlow PowerStream telemetry to watts."""
    if value is None:
        return 0.0
    normalized = float(value)
    if max_watts > 0 and abs(normalized) > max_watts * 1.5:
        if abs(normalized / 10) <= max_watts * 1.5:
            normalized = normalized / 10
    elif abs(normalized) > 1000 and abs(normalized / 10) <= 1000:
        normalized = normalized / 10
    return round(normalized, 1)


def normalize_homewizard_power_w(value: Any, *, allow_deciwatts: bool = True) -> float:
    """Normalize HomeWizard values that arrive as deciwatts in some setups."""
    numeric = _to_float(value)
    if numeric is None:
        return 0.0
    if allow_deciwatts and abs(numeric) >= 2500 and abs(numeric / 10) <= 1500:
        numeric = numeric / 10
    return round(numeric, 1)


def normalize_live_power_w(value: Any, max_expected_w: float = 4000.0) -> float:
    """Normalize live battery/solar power values to watts."""
    numeric = _to_float(value)
    if numeric is None:
        return 0.0
    if (
        max_expected_w > 0
        and abs(numeric) > max_expected_w * 1.5
        and abs(numeric / 10) <= max_expected_w * 1.5
    ):
        numeric = numeric / 10
    elif abs(numeric) >= 5000 and abs(numeric / 10) <= 1500:
        numeric = numeric / 10
    return round(numeric, 1)


def _to_float(value: Any) -> float | None:
    try:
        if value is None:
            return None
        return float(str(value).replace(",", "."))
    except (TypeError, ValueError):
        return None

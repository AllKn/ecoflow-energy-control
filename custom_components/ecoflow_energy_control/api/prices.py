"""Spot price readers."""

from __future__ import annotations

from datetime import datetime
from typing import Any

from aiohttp import ClientSession


async def fetch_prices(session: ClientSession, url: str) -> list[dict[str, Any]]:
    """Fetch hourly electricity prices from a JSON endpoint.

    The parser accepts common EPEX/day-ahead feed shapes, including Stekker,
    ENTSO-E wrappers and Enever-like records. Prices are normalized to EUR/kWh
    where the source is clearly EUR/MWh.
    """
    async with session.get(url) as resp:
        data = await resp.json(content_type=None)

    records: list[Any]
    if isinstance(data, list):
        records = data
    elif isinstance(data, dict):
        for key in ("data", "prices", "records", "items", "marketPrices"):
            if isinstance(data.get(key), list):
                records = data[key]
                break
        else:
            records = [data]
    else:
        return []

    parsed: list[dict[str, Any]] = []
    for item in records:
        if not isinstance(item, dict):
            continue
        price = _first_number(
            item,
            (
                "price_per_mwh",
                "forecast",
                "prijs",
                "price",
                "electricity_price",
                "value",
                "marketprice",
            ),
        )
        starts_at = _first_text(
            item,
            ("period_start", "datum", "datetime", "time", "start", "from", "timestamp"),
        )
        if price is None:
            continue
        if abs(price) > 5:
            price = price / 1000
        parsed.append(
            {
                "start": starts_at,
                "price_eur_kwh": round(price, 5),
                "raw": item,
            }
        )
    return parsed


def current_price(prices: list[dict[str, Any]], now: datetime) -> float | None:
    """Return the price for the current hour, falling back to first record."""
    if not prices:
        return None
    current_hour = now.replace(minute=0, second=0, microsecond=0)
    for item in prices:
        starts_at = item.get("start")
        if not starts_at:
            continue
        try:
            parsed = datetime.fromisoformat(str(starts_at).replace("Z", "+00:00"))
        except ValueError:
            continue
        if parsed.replace(minute=0, second=0, microsecond=0) == current_hour:
            return item["price_eur_kwh"]
    return prices[0]["price_eur_kwh"]


def price_bands(prices: list[dict[str, Any]]) -> dict[str, float | None]:
    """Calculate cheap and expensive bands from the current fetched market prices."""
    values = sorted(
        item["price_eur_kwh"]
        for item in prices
        if isinstance(item.get("price_eur_kwh"), (int, float))
    )
    if not values:
        return {"cheap": None, "expensive": None}
    cheap_index = max(0, round((len(values) - 1) * 0.25))
    expensive_index = min(len(values) - 1, round((len(values) - 1) * 0.75))
    return {
        "cheap": values[cheap_index],
        "expensive": values[expensive_index],
    }


def _first_number(item: dict[str, Any], keys: tuple[str, ...]) -> float | None:
    for key in keys:
        value = item.get(key)
        if value is None:
            continue
        try:
            return float(str(value).replace(",", "."))
        except ValueError:
            continue
    return None


def _first_text(item: dict[str, Any], keys: tuple[str, ...]) -> str | None:
    for key in keys:
        value = item.get(key)
        if value is not None:
            return str(value)
    return None

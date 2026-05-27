"""Weather and solar forecast reader."""

from __future__ import annotations

from datetime import datetime, timedelta
from typing import Any

from aiohttp import ClientSession


async def fetch_open_meteo_solar(
    session: ClientSession, latitude: float, longitude: float
) -> dict[str, Any]:
    """Fetch current weather and hourly solar radiation from Open-Meteo."""
    url = (
        "https://api.open-meteo.com/v1/forecast"
        f"?latitude={latitude}"
        f"&longitude={longitude}"
        "&current=temperature_2m,cloud_cover,shortwave_radiation,weather_code"
        "&hourly=temperature_2m,cloud_cover,shortwave_radiation,weather_code,precipitation_probability"
        "&forecast_days=2"
        "&timezone=Europe%2FAmsterdam"
    )
    async with session.get(url) as resp:
        data = await resp.json(content_type=None)
    return _summarize_weather(data)


def _summarize_weather(data: dict[str, Any]) -> dict[str, Any]:
    current = data.get("current") or {}
    hourly = data.get("hourly") or {}
    times = hourly.get("time") or []
    radiation = hourly.get("shortwave_radiation") or []
    clouds = hourly.get("cloud_cover") or []
    temperatures = hourly.get("temperature_2m") or []
    weather_codes = hourly.get("weather_code") or []
    precipitation = hourly.get("precipitation_probability") or []
    now = datetime.now()
    hourly_rows = []
    for index, value in enumerate(times):
        try:
            starts_at = datetime.fromisoformat(str(value))
            watts_m2 = float(radiation[index] or 0)
            cloud = float(clouds[index] or 0) if index < len(clouds) else None
            temperature = (
                float(temperatures[index]) if index < len(temperatures) else None
            )
            weather_code = int(weather_codes[index]) if index < len(weather_codes) else None
            rain_chance = (
                float(precipitation[index]) if index < len(precipitation) else None
            )
        except (TypeError, ValueError, IndexError):
            continue
        condition = _weather_condition(weather_code)
        hourly_rows.append(
            {
                "start": starts_at.isoformat(),
                "shortwave_w_m2": round(watts_m2, 1),
                "cloud_cover": cloud,
                "temperature": temperature,
                "weather_code": weather_code,
                "weather_icon": condition["icon"],
                "weather_label": condition["label"],
                "precipitation_probability": rain_chance,
            }
        )
    current_condition = _weather_condition(_int_or_none(current.get("weather_code")))

    return {
        "temperature": _float_or_none(current.get("temperature_2m")),
        "cloud_cover": _float_or_none(current.get("cloud_cover")),
        "shortwave_w_m2": _float_or_none(current.get("shortwave_radiation")),
        "weather_code": _int_or_none(current.get("weather_code")),
        "weather_icon": current_condition["icon"],
        "weather_label": current_condition["label"],
        "icon_summary": _icon_summary(hourly_rows, now, 24),
        "solar_next_4h_wh_kwp": _solar_wh_kwp(hourly_rows, now, 4),
        "solar_next_12h_wh_kwp": _solar_wh_kwp(hourly_rows, now, 12),
        "solar_next_24h_wh_kwp": _solar_wh_kwp(hourly_rows, now, 24),
        "hourly": hourly_rows[:36],
    }


def _solar_wh_kwp(rows: list[dict[str, Any]], now: datetime, hours: int) -> float:
    end = now + timedelta(hours=hours)
    total = 0.0
    for row in rows:
        starts_at = datetime.fromisoformat(str(row["start"]))
        if now.replace(minute=0, second=0, microsecond=0) <= starts_at < end:
            total += max(0.0, float(row["shortwave_w_m2"]))
    return round(total, 0)


def _float_or_none(value: Any) -> float | None:
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _int_or_none(value: Any) -> int | None:
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def _weather_condition(code: int | None) -> dict[str, str]:
    if code is None:
        return {"icon": "?", "label": "onbekend"}
    if code == 0:
        return {"icon": "☀️", "label": "zon"}
    if code in {1, 2}:
        return {"icon": "🌤️", "label": "half bewolkt"}
    if code == 3:
        return {"icon": "☁️", "label": "bewolkt"}
    if code in {45, 48}:
        return {"icon": "🌫️", "label": "mist"}
    if 51 <= code <= 67 or 80 <= code <= 82:
        return {"icon": "🌧️", "label": "regen"}
    if 71 <= code <= 77 or 85 <= code <= 86:
        return {"icon": "❄️", "label": "sneeuw"}
    if 95 <= code <= 99:
        return {"icon": "⛈️", "label": "onweer"}
    return {"icon": "🌡️", "label": "weer"}


def _icon_summary(rows: list[dict[str, Any]], now: datetime, hours: int) -> str:
    end = now + timedelta(hours=hours)
    parts = []
    for row in rows:
        starts_at = datetime.fromisoformat(str(row["start"]))
        if now.replace(minute=0, second=0, microsecond=0) <= starts_at < end:
            parts.append(f"{starts_at.strftime('%H')} {row.get('weather_icon', '?')}")
        if len(parts) >= 12:
            break
    return "  ".join(parts)

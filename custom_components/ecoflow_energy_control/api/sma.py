"""Local SMA Sunny Boy Modbus TCP reader."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from pymodbus.client import AsyncModbusTcpClient


@dataclass(frozen=True)
class SmaInverter:
    """Configured SMA inverter."""

    name: str
    host: str
    port: int = 502
    unit_id: int = 3


REGISTERS = {
    "ac_power_w": (30775, 2, 1),
    "daily_yield_wh": (30517, 4, 1),
    "total_yield_wh": (30529, 4, 1),
    "grid_frequency_hz": (30803, 2, 0.01),
}


async def read_inverter(inverter: SmaInverter) -> dict[str, Any]:
    """Read common production values from an SMA inverter via Modbus TCP."""
    client = AsyncModbusTcpClient(inverter.host, port=inverter.port)
    await client.connect()
    try:
        if not client.connected:
            return {"available": False}
        values: dict[str, Any] = {"available": True}
        for key, (address, count, scale) in REGISTERS.items():
            result = await client.read_holding_registers(
                address=address, count=count, slave=inverter.unit_id
            )
            if result.isError():
                values[key] = None
                continue
            raw = _decode_u32(result.registers)
            values[key] = raw * scale
        return values
    finally:
        client.close()


def _decode_u32(registers: list[int]) -> int:
    if len(registers) < 2:
        return 0
    value = (registers[0] << 16) + registers[1]
    if value in (0xFFFFFFFF, 0x80000000):
        return 0
    return value


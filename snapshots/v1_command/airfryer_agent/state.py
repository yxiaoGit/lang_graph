"""Simulated air fryer hardware state."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


@dataclass
class AirFryerState:
    power_on: bool = False
    current_temp_c: int = 25
    target_temp_c: int = 25
    contents: str = "empty"
    log: list[str] = field(default_factory=list)

    def record(self, message: str) -> str:
        entry = f"[{_now_iso()}] {message}"
        self.log.append(entry)
        return entry

    def describe(self) -> str:
        power = "ON" if self.power_on else "OFF"
        return (
            f"power={power} temp={self.current_temp_c}C "
            f"target={self.target_temp_c}C contents={self.contents}"
        )


# Module-level simulated hardware. Tools mutate this so the CLI, agent,
# and LangChain tool calls all observe the same fryer.
_fryer = AirFryerState()


def get_fryer() -> AirFryerState:
    return _fryer


def reset_fryer() -> AirFryerState:
    global _fryer
    _fryer = AirFryerState()
    return _fryer

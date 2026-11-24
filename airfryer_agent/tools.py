"""LangChain tools that operate the simulated air fryer."""

from __future__ import annotations

try:
    from langchain_core.tools import tool
except ImportError:  # pragma: no cover - lets tests import without install
    def tool(func):  # type: ignore[no-redef]
        func.name = getattr(func, "__name__", "tool")
        return func

from .state import get_fryer


@tool
def preheat(temp_c: int, minutes: float) -> str:
    """Preheat the air fryer to temp_c for minutes. Call before adding food."""
    fryer = get_fryer()
    fryer.power_on = True
    fryer.target_temp_c = int(temp_c)
    fryer.current_temp_c = int(temp_c)
    return fryer.record(f"preheat to {int(temp_c)}C for {minutes} min")


@tool
def add_food(food: str) -> str:
    """Put food into the air fryer basket. Call after preheat."""
    fryer = get_fryer()
    if not fryer.power_on:
        return fryer.record("add_food refused: fryer is OFF, preheat first")
    fryer.contents = food
    return fryer.record(f"added food: {food}")


@tool
def turn_food() -> str:
    """Turn / flip / shake the food mid-cook for even browning."""
    fryer = get_fryer()
    if fryer.contents == "empty":
        return fryer.record("turn_food refused: basket is empty")
    return fryer.record(f"turned food: {fryer.contents}")


@tool
def power_off() -> str:
    """Turn the air fryer off at the end of cooking."""
    fryer = get_fryer()
    fryer.power_on = False
    fryer.target_temp_c = 25
    fryer.current_temp_c = 25
    return fryer.record("powered OFF")


@tool
def get_status() -> str:
    """Read the current air fryer status (power, temp, contents)."""
    fryer = get_fryer()
    status = fryer.describe()
    fryer.record(f"status check: {status}")
    return status


TOOLS = [preheat, add_food, turn_food, power_off, get_status]


def call_tool(name: str, *args, **kwargs) -> str:
    """Invoke a tool by name through its LangChain interface."""
    mapping = {t.name: t for t in TOOLS}
    if name not in mapping:
        raise KeyError(f"unknown tool {name!r}")
    result = mapping[name].invoke(*args, **kwargs)  # type: ignore[union-attr]
    return str(result)

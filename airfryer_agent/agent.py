"""Agent: cooks a dish via LangGraph, stopping for the user at each timed action."""

from __future__ import annotations

import time
from collections.abc import Callable
from dataclasses import dataclass

from .recipes import Recipe, get_recipe
from .tools import TOOLS

HumanGate = Callable[[str], str]


@dataclass
class CookEvent:
    kind: str  # tool | wait | stop | done | cancel
    message: str


@dataclass
class PlanStep:
    kind: str  # tool | wait | stop
    message: str
    tool: str = ""
    tool_args: dict | None = None
    wait_min: float = 0.0


def build_plan(recipe: Recipe) -> list[PlanStep]:
    """Compile a recipe into tool calls, timed waits, and human stops."""
    steps: list[PlanStep] = [
        PlanStep(
            kind="tool",
            message=f"Preheat to {recipe.preheat_temp_c}C",
            tool="preheat",
            tool_args={"temp_c": recipe.preheat_temp_c, "minutes": recipe.preheat_min},
        ),
        PlanStep(kind="wait", message="Preheating", wait_min=recipe.preheat_min),
        PlanStep(
            kind="stop",
            message=(
                f"Preheat done ({recipe.preheat_temp_c}C). "
                f"Add {recipe.load} ({recipe.label}), then continue."
            ),
        ),
        PlanStep(
            kind="tool",
            message=f"Add {recipe.load}",
            tool="add_food",
            tool_args={"food": f"{recipe.label} ({recipe.load})"},
        ),
    ]
    if recipe.turn_after_min is None:
        steps += [
            PlanStep(
                kind="wait",
                message=f"Cooking at {recipe.cook_temp_c}C",
                wait_min=recipe.cook_min,
            ),
        ]
    else:
        first = min(recipe.turn_after_min, recipe.cook_min)
        rest = recipe.cook_min - first
        steps += [
            PlanStep(
                kind="wait",
                message=f"Cooking at {recipe.cook_temp_c}C (part 1)",
                wait_min=first,
            ),
            PlanStep(
                kind="stop",
                message=(
                    f"Timer: turn/shake {recipe.load} now "
                    f"({rest:.1f} min left), then continue."
                ),
            ),
            PlanStep(kind="tool", message="Turn food", tool="turn_food"),
            PlanStep(
                kind="wait",
                message=f"Cooking at {recipe.cook_temp_c}C (part 2)",
                wait_min=rest,
            ),
        ]
    steps += [
        PlanStep(
            kind="stop",
            message=(
                f"{recipe.label} done. Remove food from basket, then continue "
                "to power off."
            ),
        ),
        PlanStep(kind="tool", message="Power off", tool="power_off"),
    ]
    return steps


CONTINUE_WORDS = {"", "done", "yes", "y", "ok", "continue", "go"}
CANCEL_WORDS = {"cancel", "abort", "quit", "q"}


def console_gate(prompt: str) -> str:
    """Prompt the user at a stop; returns normalized 'done' or 'cancel'."""
    print(f"\n[ACTION REQUIRED] {prompt}")
    print("Do the step, then type: <Enter>/done/yes to continue, cancel to abort.")
    while True:
        try:
            answer = input("> ").strip().lower()
        except EOFError:
            print("(no input - treating as cancel)")
            return "cancel"
        if answer in CONTINUE_WORDS:
            return "done"
        if answer in CANCEL_WORDS:
            return "cancel"
        print(f"Unrecognized {answer!r}: type 'done' to continue or 'cancel' to abort.")


def auto_gate(prompt: str) -> str:
    print(f"[auto-confirmed stop] {prompt}")
    return "done"


class AirFryerAgent:
    """LangChain-tool agent with timed human-in-the-loop stops."""

    def __init__(
        self,
        human_gate: HumanGate | None = None,
        sim_min_to_real_sec: float = 1.0,
        sleep: Callable[[float], None] | None = None,
    ) -> None:
        self.human_gate = human_gate or console_gate
        self.sim_min_to_real_sec = sim_min_to_real_sec
        self._sleep = sleep or time.sleep

    @property
    def tools(self):
        return TOOLS

    def cook(self, dish: str, fresh: bool = True) -> list[CookEvent]:
        from .graph import run_cook_graph

        get_recipe(dish)  # validate early for a clean KeyError
        raw = run_cook_graph(
            dish,
            human_gate=self.human_gate,
            scale=self.sim_min_to_real_sec,
            sleep=self._sleep,
            fresh=fresh,
        )
        return [CookEvent(kind=e["kind"], message=e["message"]) for e in raw]

    def invoke(self, dish: str, auto_yes: bool = False) -> list[CookEvent]:
        if auto_yes:
            self.human_gate = auto_gate
        return self.cook(dish)

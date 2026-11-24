"""LangGraph orchestration for the air fryer simulator (v2).

Conditional-edges style: each `ask_*` node pauses with `interrupt()` and
stores the reply in state; a routing function then picks the next node.
Unlike `Command(goto=...)`, these branches render in get_graph diagrams.
"""

from __future__ import annotations

import operator
import time
import uuid
from collections.abc import Callable
from typing import Annotated

from langgraph.checkpoint.memory import InMemorySaver
from langgraph.graph import END, START, StateGraph
from langgraph.types import Command, interrupt
from typing_extensions import TypedDict

from .agent import CANCEL_WORDS
from .recipes import get_recipe
from .state import get_fryer, reset_fryer
from .tools import call_tool


class CookState(TypedDict):
    dish: str
    scale: float
    events: Annotated[list[dict], operator.add]
    cancelled: bool
    decision: str  # last human reply (or "skip" when no stop applies)


def _ev(kind: str, message: str) -> dict:
    return {"kind": kind, "message": message}


def _is_cancel(decision: str) -> bool:
    return decision.strip().lower() in CANCEL_WORDS


def print_cook_graph(compiled) -> str:
    """Print nodes, edges, and ASCII + mermaid diagrams of the cook graph."""
    drawable = compiled.get_graph()
    nodes = sorted(n.id for n in drawable.nodes.values())
    lines = ["--- cook graph ---", f"nodes: {', '.join(nodes)}", "edges:"]
    for e in drawable.edges:
        tag = "conditional" if getattr(e, "conditional", False) else "static"
        lines.append(f"  {e.source} -> {e.target} [{tag}]")
    lines.append("conditional routes:")
    lines.append("  ask_add -> add_food | cancelled")
    lines.append("  ask_turn -> turn | ask_done | cancelled")
    lines.append("  ask_done -> finish | cancelled")
    try:
        lines.append(drawable.draw_ascii())
    except ImportError:
        lines.append("(install grandalf for ASCII diagram; pip install grandalf)")
    lines.append("mermaid (paste into mermaid.live or any markdown viewer):")
    lines.append("```mermaid")
    lines.append(drawable.draw_mermaid())
    lines.append("```")
    text = "\n".join(lines)
    print(text)
    return text


def build_cook_graph(
    sleep: Callable[[float], None] | None = None, show: bool = True
):
    """Build the cook StateGraph. sleep is injected for fast tests."""
    do_sleep = sleep or time.sleep

    def n_preheat(state: CookState) -> dict:
        recipe = get_recipe(state["dish"])
        result = call_tool(
            "preheat",
            {"temp_c": recipe.preheat_temp_c, "minutes": recipe.preheat_min},
        )
        msg = f"Preheat to {recipe.preheat_temp_c}C -> {result}"
        print(msg)
        real = recipe.preheat_min * state["scale"]
        wmsg = f"Preheating: {recipe.preheat_min} simulated min ({real:.1f}s real)"
        print(wmsg)
        do_sleep(real)
        return {"events": [_ev("tool", msg), _ev("wait", wmsg)]}

    def n_ask_add(state: CookState) -> dict:
        recipe = get_recipe(state["dish"])
        prompt = (
            f"Preheat done ({recipe.preheat_temp_c}C). "
            f"Add {recipe.load} ({recipe.label}), then continue."
        )
        answer = interrupt(prompt)
        return {"decision": str(answer), "events": [_ev("stop", prompt)]}

    def route_add(state: CookState) -> str:
        return "cancelled" if _is_cancel(state["decision"]) else "add_food"

    def n_add_food(state: CookState) -> dict:
        recipe = get_recipe(state["dish"])
        result = call_tool("add_food", {"food": f"{recipe.label} ({recipe.load})"})
        msg = f"Add {recipe.load} -> {result}"
        print(msg)
        return {"events": [_ev("tool", msg)]}

    def n_cook1(state: CookState) -> dict:
        recipe = get_recipe(state["dish"])
        part = recipe.cook_min if recipe.turn_after_min is None else min(
            recipe.turn_after_min, recipe.cook_min
        )
        suffix = f"{recipe.cook_temp_c}C" if recipe.turn_after_min is None else (
            f"{recipe.cook_temp_c}C (part 1)"
        )
        real = part * state["scale"]
        wmsg = f"Cooking at {suffix}: {part} simulated min ({real:.1f}s real)"
        print(wmsg)
        do_sleep(real)
        return {"events": [_ev("wait", wmsg)]}

    def n_ask_turn(state: CookState) -> dict:
        recipe = get_recipe(state["dish"])
        if recipe.turn_after_min is None:
            return {"decision": "skip", "events": []}
        first = min(recipe.turn_after_min, recipe.cook_min)
        rest = recipe.cook_min - first
        prompt = (
            f"Timer: turn/shake {recipe.load} now "
            f"({rest:.1f} min left), then continue."
        )
        answer = interrupt(prompt)
        return {"decision": str(answer), "events": [_ev("stop", prompt)]}

    def route_turn(state: CookState) -> str:
        if state["decision"] == "skip":
            return "ask_done"
        if _is_cancel(state["decision"]):
            return "cancelled"
        return "turn"

    def n_turn(state: CookState) -> dict:
        result = call_tool("turn_food", {})
        msg = f"Turn food -> {result}"
        print(msg)
        return {"events": [_ev("tool", msg)]}

    def n_cook2(state: CookState) -> dict:
        recipe = get_recipe(state["dish"])
        if recipe.turn_after_min is None:
            return {"events": []}
        first = min(recipe.turn_after_min, recipe.cook_min)
        rest = recipe.cook_min - first
        real = rest * state["scale"]
        wmsg = (
            f"Cooking at {recipe.cook_temp_c}C (part 2): "
            f"{rest} simulated min ({real:.1f}s real)"
        )
        print(wmsg)
        do_sleep(real)
        return {"events": [_ev("wait", wmsg)]}

    def n_ask_done(state: CookState) -> dict:
        recipe = get_recipe(state["dish"])
        prompt = (
            f"{recipe.label} done. Remove food from basket, then continue "
            "to power off."
        )
        answer = interrupt(prompt)
        return {"decision": str(answer), "events": [_ev("stop", prompt)]}

    def route_done(state: CookState) -> str:
        return "cancelled" if _is_cancel(state["decision"]) else "finish"

    def n_finish(state: CookState) -> dict:
        recipe = get_recipe(state["dish"])
        result = call_tool("power_off", {})
        msg = f"Power off -> {result}"
        print(msg)
        fryer = get_fryer()
        done = f"finished {recipe.label}: {fryer.describe()}"
        return {"events": [_ev("tool", msg), _ev("done", done)]}

    def n_cancelled(state: CookState) -> dict:
        call_tool("power_off", {})
        return {"events": [_ev("cancel", "cancelled by user")], "cancelled": True}

    g = StateGraph(CookState)
    g.add_node("preheat", n_preheat)
    g.add_node("ask_add", n_ask_add)
    g.add_node("add_food", n_add_food)
    g.add_node("cook1", n_cook1)
    g.add_node("ask_turn", n_ask_turn)
    g.add_node("turn", n_turn)
    g.add_node("cook2", n_cook2)
    g.add_node("ask_done", n_ask_done)
    g.add_node("finish", n_finish)
    g.add_node("cancelled", n_cancelled)

    g.add_edge(START, "preheat")
    g.add_edge("preheat", "ask_add")
    g.add_conditional_edges(
        "ask_add", route_add, {"add_food": "add_food", "cancelled": "cancelled"}
    )
    g.add_edge("add_food", "cook1")
    g.add_edge("cook1", "ask_turn")
    g.add_conditional_edges(
        "ask_turn",
        route_turn,
        {"turn": "turn", "ask_done": "ask_done", "cancelled": "cancelled"},
    )
    g.add_edge("turn", "cook2")
    g.add_edge("cook2", "ask_done")
    g.add_conditional_edges(
        "ask_done", route_done, {"finish": "finish", "cancelled": "cancelled"}
    )
    g.add_edge("finish", END)
    g.add_edge("cancelled", END)
    compiled = g.compile(checkpointer=InMemorySaver())
    if show:
        print_cook_graph(compiled)
    return compiled


def run_cook_graph(
    dish: str,
    human_gate: Callable[[str], str],
    scale: float = 1.0,
    sleep: Callable[[float], None] | None = None,
    fresh: bool = True,
) -> list[dict]:
    """Run the graph, pausing at each interrupt for the human gate."""
    get_recipe(dish)  # validate early for a clean KeyError
    if fresh:
        reset_fryer()
    graph = build_cook_graph(sleep=sleep)
    config = {"configurable": {"thread_id": uuid.uuid4().hex}}
    state = graph.invoke(
        {"dish": dish, "scale": scale, "events": [], "cancelled": False, "decision": ""},
        config,
    )
    while "__interrupt__" in state and state["__interrupt__"]:
        prompt = str(state["__interrupt__"][0].value)
        answer = human_gate(prompt)
        state = graph.invoke(Command(resume=answer), config)
    return list(state.get("events", []))

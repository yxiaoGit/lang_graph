"""Offline tests for the air fryer agent (no network, no API keys)."""

from airfryer_agent.agent import AirFryerAgent, build_plan
from airfryer_agent.recipes import RECIPES, get_recipe
from airfryer_agent.state import get_fryer, reset_fryer
from airfryer_agent.tools import TOOLS


def test_all_recipes_have_valid_plan():
    for name in RECIPES:
        plan = build_plan(get_recipe(name))
        kinds = [s.kind for s in plan]
        assert kinds[0] == "tool"
        assert "stop" in kinds
        assert kinds[-1] == "tool"  # power_off
        stops = [s for s in plan if s.kind == "stop"]
        assert len(stops) in (2, 3)


def test_salmon_skips_turn_stop():
    plan = build_plan(get_recipe("salmon_fillet"))
    assert len([s for s in plan if s.kind == "stop"]) == 2
    assert not [s for s in plan if s.tool == "turn_food"]


def test_fries_has_turn_stop_midway():
    plan = build_plan(get_recipe("french_fries"))
    assert len([s for s in plan if s.kind == "stop"]) == 3
    assert [s for s in plan if s.tool == "turn_food"]


def test_langchain_tools_exposed():
    names = sorted(t.name for t in TOOLS)
    assert names == ["add_food", "get_status", "power_off", "preheat", "turn_food"]


def test_full_cook_auto_confirmed():
    reset_fryer()
    agent = AirFryerAgent(human_gate=lambda prompt: "done", sim_min_to_real_sec=0,
                          sleep=lambda s: None)
    events = agent.cook("french_fries")
    kinds = [e.kind for e in events]
    assert kinds.count("stop") == 3
    assert kinds[-1] == "done"
    assert get_fryer().power_on is False


def test_cancel_powers_off():
    reset_fryer()
    agent = AirFryerAgent(human_gate=lambda prompt: "cancel", sim_min_to_real_sec=0,
                          sleep=lambda s: None)
    events = agent.cook("veggie_mix")
    assert events[-1].kind == "cancel"
    assert get_fryer().power_on is False


def test_console_gate_inputs(monkeypatch):
    from airfryer_agent.agent import console_gate

    monkeypatch.setattr("builtins.input", lambda *a: "yes")
    assert console_gate("do X") == "done"
    monkeypatch.setattr("builtins.input", lambda *a: "")
    assert console_gate("do X") == "done"
    monkeypatch.setattr("builtins.input", lambda *a: "CANCEL")
    assert console_gate("do X") == "cancel"
    answers = iter(["huh?", "done"])
    monkeypatch.setattr("builtins.input", lambda *a: next(answers))
    assert console_gate("do X") == "done"

    def boom(*a):
        raise EOFError

    monkeypatch.setattr("builtins.input", boom)
    assert console_gate("do X") == "cancel"


def test_print_cook_graph_includes_diagrams(capsys):
    from airfryer_agent.graph import build_cook_graph, print_cook_graph

    text = print_cook_graph(build_cook_graph(show=False))
    assert "nodes:" in text and "preheat" in text
    assert "__start__ -> preheat" in text
    assert "ask_add -> add_food | cancelled" in text
    assert "```mermaid" in text and "graph TD;" in text
    assert "preheat --> ask_add;" in text
    capsys.readouterr()

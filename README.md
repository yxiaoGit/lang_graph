# Air Fryer Simulator Agent (LangGraph, v2)

LangGraph agent that cooks different dishes and **stops at each timed
action** so you can do the physical step, like a real air fryer.

Flow per dish: `preheat` → wait → **STOP: add food** → `add_food` →
cook → **STOP: turn food** → `turn_food` → cook rest →
**STOP: remove food** → `power_off`. Salmon skips the turn stop.

Routing uses `add_conditional_edges`: each `ask_*` node pauses with
`interrupt()`, stores your reply in state, and a router picks the next
node. (The earlier `Command(goto=...)` version is saved under
`snapshots/v1_command/`.)

## Setup

Run from this folder (`lang_graph/`):

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -e .
```

## Run

```bash
source .venv/bin/activate
python -m airfryer_agent.cli list
python -m airfryer_agent.cli cook french_fries --speed 0   # interactive stops
python -m airfryer_agent.cli cook chicken_wings --yes      # auto-confirm stops
```

- `--yes` auto-answers `done` at every stop; without it the agent waits.
- `--speed 0` skips simulated waiting; default `--fast` maps 1 simulated
  minute to 1 real second; `--realtime` uses 60s.

## What to type at each stop

The agent prints `[ACTION REQUIRED]` and waits:

- continue: press `<Enter>`, or type `done`, `yes`, `y`, `ok`, `continue`, `go`
- stop/cancel: type `cancel` (`abort`, `quit`, `q` also work) — powers off
- anything else is reprompted; closed stdin counts as cancel

## Graph diagram

Every `cook` prints the compiled graph. Standalone:

```bash
python -m airfryer_agent.cli graph --format mermaid   # or ascii, both
```

To view the flowchart:

1. Copy the fenced ` ```mermaid ` block from the output.
2. Open <https://mermaid.live> in a browser.
3. Paste into the left editor — the diagram renders on the right.

Direct builtin (same output, no CLI):

```bash
python -c "from airfryer_agent.graph import build_cook_graph; print(build_cook_graph(show=False).get_graph().draw_mermaid())"
```

## Tests

```bash
source .venv/bin/activate
pip install pytest
python -m pytest tests/ -q
```

Offline, no API keys needed.

## Layout

- `airfryer_agent/recipes.py` — 5 dish profiles (preheat/cook/turn times)
- `airfryer_agent/state.py` — simulated fryer hardware state
- `airfryer_agent/tools.py` — LangChain `@tool`s: preheat, add_food, turn_food, power_off, get_status
- `airfryer_agent/graph.py` — LangGraph StateGraph: `interrupt()` stops + conditional-edge routing
- `airfryer_agent/agent.py` — input gates (`done`/`cancel`) + `AirFryerAgent` (runs the graph)
- `airfryer_agent/cli.py` — `list` / `cook` / `graph` CLI
- `tests/test_agent.py` — offline tests
- `snapshots/v1_command/` — v1 snapshot (`Command`-based routing) with its own README

## Graph

<img width="1374" height="1610" alt="image" src="https://github.com/user-attachments/assets/9562fe0a-ae46-4ae5-af99-3ab3594c6d85" />

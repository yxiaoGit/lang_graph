# Air Fryer Simulator Agent

LangChain-tool agent that cooks different dishes and **stops at each timed
action** so the user can do the physical step, like a real air fryer.

Flow per dish: `preheat` -> wait -> **STOP: add food** -> `add_food` ->
cook -> **STOP: turn food** -> `turn_food` -> cook rest ->
**STOP: remove food** -> `power_off`. Salmon skips the turn stop.

## Setup (project-local env)

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -e .
```

Or with uv: `uv venv && uv pip install -e .`, then prefix with `uv run`.

## Use

```bash
source .venv/bin/activate
python -m airfryer_agent.cli list
python -m airfryer_agent.cli cook french_fries        # interactive stops
python -m airfryer_agent.cli cook chicken_wings --yes # auto-confirm stops
python -m airfryer_agent.cli cook veggie_mix --yes --speed 0.1
```

At each stop the agent prints `[ACTION REQUIRED]` and waits for input:

- continue: press `<Enter>`, or type `done`, `yes`, `y`, `ok`, `continue`, `go`
- stop/cancel: type `cancel` (`abort`, `quit`, `q` also work) — powers off
- anything else is reprompted; closed stdin counts as cancel

`--fast` (default) maps 1 simulated minute to 1 real second; `--realtime`
uses 60s. `--yes` auto-answers `done` at every stop.

## Layout

- `airfryer_agent/recipes.py` - 5 dish profiles (preheat/cook/turn times)
- `airfryer_agent/state.py` - simulated fryer hardware state
- `airfryer_agent/tools.py` - LangChain `@tool`s: preheat, add_food, turn_food, power_off, get_status
- `airfryer_agent/graph.py` - LangGraph StateGraph with `interrupt()` human stops
- `airfryer_agent/agent.py` - plan builder + `AirFryerAgent` (runs the graph)
- `airfryer_agent/cli.py` - `list` / `cook` CLI
- `tests/test_agent.py` - offline tests (no network, no API keys)

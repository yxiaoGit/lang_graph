# Air Fryer Simulator Agent — v1 snapshot (Command-based routing)

Saved copy of the agent before the conditional-edges refactor. Behavior
is the same (preheat → add → turn → finish with human stops); only the
graph routing differs: the `ask_*` nodes return `Command(goto=...)`
instead of using `add_conditional_edges` with routers.

Known v1 limitation: `get_graph()` cannot see `Command` jumps, so the
ASCII/mermaid diagram renders only up to `ask_add`. Runtime routing is
unaffected.

## Run

v1 has no env of its own; use the main project's env with `PYTHONPATH`.
Run from any directory **outside** the workspace root (so CWD doesn't
shadow the snapshot). With project root
`/Users/yingxiao/hertz-HTZ-T16475/attempt1/lang_graph`:

```bash
cd /tmp
VENV=/Users/yingxiao/hertz-HTZ-T16475/attempt1/lang_graph/.venv
export PYTHONPATH=/Users/yingxiao/hertz-HTZ-T16475/attempt1/lang_graph/snapshots/v1_command
$VENV/bin/python -m airfryer_agent.cli list
$VENV/bin/python -m airfryer_agent.cli cook french_fries --yes --speed 0
$VENV/bin/python -m airfryer_agent.cli graph --format mermaid
```

Inputs at stops: `<Enter>`/`done`/`yes` continues, `cancel` aborts.

## Diagram

`graph --format mermaid` prints a fenced mermaid block; paste it into
<https://mermaid.live> to view. Expect the partial diagram noted above —
compare with v2's full diagram from the project root README.

"""CLI for the air fryer simulator agent."""

from __future__ import annotations

import argparse
import sys

from .agent import AirFryerAgent, auto_gate, console_gate
from .recipes import list_recipes


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description="LangChain air fryer simulator agent")
    sub = p.add_subparsers(dest="command", required=True)

    sub.add_parser("list", help="list available dishes")

    graph_cmd = sub.add_parser("graph", help="print the cook graph diagram")
    graph_cmd.add_argument(
        "--format", choices=["ascii", "mermaid", "both"], default="both"
    )

    cook = sub.add_parser("cook", help="cook a dish with human-in-the-loop stops")
    cook.add_argument("dish", help="dish name (see 'list')")
    cook.add_argument(
        "--yes", action="store_true", help="auto-confirm every stop (no prompts)"
    )
    speed = cook.add_mutually_exclusive_group()
    speed.add_argument(
        "--fast",
        action="store_true",
        default=True,
        help="1 simulated minute = 1 real second (default)",
    )
    speed.add_argument(
        "--realtime",
        action="store_true",
        help="1 simulated minute = 60 real seconds",
    )
    cook.add_argument(
        "--speed",
        type=float,
        default=None,
        help="explicit real seconds per simulated minute (overrides --fast/--realtime)",
    )
    return p


def cmd_list() -> int:
    print("Available dishes:")
    for r in list_recipes():
        turn = "no turn" if r.turn_after_min is None else f"turn after {r.turn_after_min}m"
        print(
            f"  {r.name:15s} {r.label:15s} "
            f"preheat {r.preheat_temp_c}C/{r.preheat_min}m "
            f"cook {r.cook_temp_c}C/{r.cook_min}m {turn}"
        )
    return 0


def cmd_cook(args: argparse.Namespace) -> int:
    if args.speed is not None:
        scale = args.speed
    elif args.realtime:
        scale = 60.0
    else:
        scale = 1.0
    gate = auto_gate if args.yes else console_gate
    agent = AirFryerAgent(human_gate=gate, sim_min_to_real_sec=scale)
    try:
        events = agent.cook(args.dish)
    except KeyError as e:
        print(str(e), file=sys.stderr)
        return 2
    print("\n--- session log ---")
    for ev in events:
        print(f"[{ev.kind}] {ev.message}")
    cancelled = any(ev.kind == "cancel" for ev in events)
    return 1 if cancelled else 0


def cmd_graph(args: argparse.Namespace) -> int:
    from .graph import build_cook_graph

    drawable = build_cook_graph(show=False).get_graph()
    if args.format in ("ascii", "both"):
        try:
            print(drawable.draw_ascii())
        except ImportError:
            print("(install grandalf for ASCII diagram; pip install grandalf)")
    if args.format in ("mermaid", "both"):
        print("```mermaid")
        print(drawable.draw_mermaid())
        print("```")
    return 0


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    if args.command == "list":
        return cmd_list()
    if args.command == "cook":
        return cmd_cook(args)
    if args.command == "graph":
        return cmd_graph(args)
    return 2


if __name__ == "__main__":
    raise SystemExit(main())

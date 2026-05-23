"""CLI demo: `python -m mafia.cli --players 6` runs an AI-vs-AI game in the terminal."""

from __future__ import annotations

import argparse
import random
import sys
from typing import Any

from rich.console import Console
from rich.panel import Panel

from mafia.agents.llm_agent import LLMAgent
from mafia.agents.personas import load_personas
from mafia.engine import run_game, setup_game
from mafia.llm.claude_client import ClaudeClient
from mafia.models import GameState, Role, Team
from mafia.player import PlayerInterface

# Module-level console for interactive use; tests override via run_demo(console=...)
_CONSOLE = Console(file=sys.stdout)


def _make_client() -> ClaudeClient:
    return ClaudeClient()


def build_agents_for_state(
    state: GameState, *, client: Any, rng: random.Random
) -> dict[str, LLMAgent]:
    pool = load_personas()
    drawn = pool.draw(len(state.players), rng=rng)
    agents: dict[str, LLMAgent] = {}
    for player, persona in zip(state.players, drawn, strict=True):
        # Rename player using persona for readability in logs.
        player.name = persona.name
        agents[player.id] = LLMAgent(actor=player, persona=persona, client=client)
    return agents


def _print_setup(state: GameState, console: Console) -> None:
    rows = []
    for p in state.players:
        role_hint = "(혼자만 알려진 역할)" if p.role != Role.CIVILIAN else ""
        rows.append(f"  {p.id} {p.name} [{p.role.value}] {role_hint}")
    console.print(Panel("\n".join(rows), title="플레이어 (디버그용)", border_style="dim"))


def _print_log_tail(state: GameState, since: int, console: Console) -> int:
    for e in state.public_log[since:]:
        kind = e.get("kind")
        if kind == "speak":
            speaker = state.player_by_id(e["speaker_id"]).name
            console.print(f"[cyan]{speaker}[/]: {e['text']}")
        elif kind == "speak_freetalk":
            speaker = state.player_by_id(e["speaker_id"]).name
            console.print(f"[cyan]{speaker}[/] (자유): {e['text']}")
        elif kind == "vote_nominate":
            voter = state.player_by_id(e["voter_id"]).name
            target_id = e["target_id"]
            target = (
                state.player_by_id(target_id).name
                if any(p.id == target_id for p in state.players)
                else target_id
            )
            console.print(f"  [yellow]{voter}[/] 지명 → [bold]{target}[/]")
        elif kind == "vote_updown":
            voter = state.player_by_id(e["voter_id"]).name
            vote = e["vote"]
            color = "green" if vote == "yes" else "red"
            console.print(f"  [{color}]{voter}: {vote}[/]")
        elif kind == "last_words":
            speaker = state.player_by_id(e["speaker_id"]).name
            console.print(f"[magenta]{speaker} 최후변론[/]: {e['text']}")
        elif kind == "execution":
            victim = state.player_by_id(e["candidate_id"]).name
            console.print(f"[bold red]💀 처형: {victim} (찬성 {e['yes']} vs 반대 {e['no']})[/]")
    return len(state.public_log)


class _LoggingActors(dict):
    """Wraps actors so each decide() prints a brief marker between phases."""


def run_demo(
    *,
    player_count: int,
    seed: int,
    client: Any,
    max_days: int = 20,
    console: Console | None = None,
) -> str:
    # Create a fresh console pointing to current sys.stdout so capsys can capture it.
    if console is None:
        console = Console(file=sys.stdout)

    rng = random.Random(seed)
    state = setup_game(player_count=player_count, rng=rng)
    actors: dict[str, PlayerInterface] = build_agents_for_state(state, client=client, rng=rng)

    _print_setup(state, console)
    console.rule("[bold]Day 1 — 첫 번째 밤[/]")

    # Simpler MVP: run the entire game then dump the log day-by-day.
    winner = run_game(state, actors, max_days=max_days)

    # Stream log retrospectively, day-by-day
    current_day = 1
    console.rule(f"[bold]Day {current_day} 진행[/]")
    for i, e in enumerate(state.public_log):
        day = e.get("day_number", current_day)
        if day != current_day:
            current_day = day
            console.rule(f"[bold]Day {current_day}[/]")
        # Print the entry using same handler
        _print_log_tail(state, i, console)

    console.rule("[bold red]GAME OVER[/]")
    if state.winner == Team.MAFIA:
        console.print("[bold red]마피아 승리![/]")
    elif state.winner == Team.CITIZEN:
        console.print("[bold green]시민 승리![/]")
    else:
        console.print(f"[yellow]게임 종료 ({winner})[/]")

    # Reveal roles
    rows = [
        f"  {p.id} {p.name}: {p.role.value} ({'생존' if p.alive else '사망'})"
        for p in state.players
    ]
    console.print(Panel("\n".join(rows), title="역할 공개", border_style="dim"))
    return winner


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="mafia-cli")
    parser.add_argument("--players", type=int, default=6, help="4~11")
    parser.add_argument("--seed", type=int, default=0)
    parser.add_argument("--max-days", type=int, default=20)
    args = parser.parse_args(argv)
    client = _make_client()
    try:
        run_demo(
            player_count=args.players,
            seed=args.seed,
            client=client,
            max_days=args.max_days,
        )
    except KeyboardInterrupt:
        _CONSOLE.print("\n[yellow]중단되었습니다.[/]")
        return 130
    return 0


if __name__ == "__main__":
    sys.exit(main())

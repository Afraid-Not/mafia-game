"""CLI demo: `python -m mafia.cli --players 6` runs an AI-vs-AI game in the terminal."""

from __future__ import annotations

import argparse
import random
import sys
from typing import Any

from rich.console import Console
from rich.markup import escape
from rich.panel import Panel

from mafia.agents.llm_agent import LLMAgent
from mafia.agents.personas import load_personas
from mafia.engine import run_game, setup_game
from mafia.llm.claude_client import ClaudeClient
from mafia.models import GameState, Team
from mafia.player import PlayerInterface


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


def _print_setup(state: GameState, jobs: dict[str, str], console: Console) -> None:
    rows = []
    for p in state.players:
        job = jobs.get(p.id, "")
        label = f"{p.name}({job})" if job else p.name
        rows.append(f"  {p.id} {label} [{p.role.value}]")
    console.print(Panel("\n".join(rows), title="역할 (디버그)", border_style="dim"))


class _StreamingLog(list):
    """Subclass of list that fires a callback after each append.

    Used to hook into GameEngine's `state.public_log.append(...)` so that the CLI
    can print events as they happen — without changing the engine's API.
    """

    def __init__(self, on_append):
        super().__init__()
        self._on_append = on_append

    def append(self, item: dict) -> None:  # type: ignore[override]
        super().append(item)
        self._on_append(item)


def _name_with_job(state: GameState, jobs: dict[str, str], pid: str) -> str:
    for p in state.players:
        if p.id == pid:
            job = jobs.get(pid)
            return f"{p.name}({job})" if job else p.name
    return pid


def _print_event(
    state: GameState,
    e: dict,
    console: Console,
    day_ref: dict,
    jobs: dict[str, str],
) -> None:
    day = e.get("day_number", day_ref["current"])
    if day != day_ref["current"]:
        day_ref["current"] = day
        console.rule(f"[bold]Day {day}[/]")

    kind = e.get("kind")
    if kind == "speak":
        speaker = _name_with_job(state, jobs, e["speaker_id"])
        console.print(f"[cyan]{escape(speaker)}[/]: {escape(e['text'])}")
    elif kind == "speak_freetalk":
        speaker = _name_with_job(state, jobs, e["speaker_id"])
        console.print(f"[cyan]{escape(speaker)}[/] (자유): {escape(e['text'])}")
    elif kind == "last_words":
        speaker = _name_with_job(state, jobs, e["speaker_id"])
        console.print(f"[magenta]{escape(speaker)} 최후변론[/]: {escape(e['text'])}")
    elif kind == "vote_nominate":
        voter = _name_with_job(state, jobs, e["voter_id"])
        target = _name_with_job(state, jobs, e["target_id"])
        console.print(f"  [yellow]{escape(voter)}[/] 지명 → [bold]{escape(target)}[/]")
    elif kind == "vote_updown":
        voter = _name_with_job(state, jobs, e["voter_id"])
        vote = e["vote"]
        color = "green" if vote == "yes" else "red"
        console.print(f"  [{color}]{escape(voter)}: {vote}[/]")
    elif kind == "execution":
        victim = _name_with_job(state, jobs, e["candidate_id"])
        role = e.get("role", "?")
        console.print(
            f"[bold red]💀 처형: {escape(victim)} — 역할은 ({role})였습니다. "
            f"(찬성 {e['yes']} vs 반대 {e['no']})[/]"
        )
    elif kind == "pardon":
        spared = _name_with_job(state, jobs, e["candidate_id"])
        console.print(
            f"[bold green]✅ 무죄 방면: {escape(spared)} (찬성 {e['yes']} vs 반대 {e['no']})[/]"
        )
    elif kind == "night_death":
        victim = _name_with_job(state, jobs, e["victim_id"])
        role = e.get("victim_role", "?")
        console.print(
            f"[bold red]🌙 밤 동안 {escape(victim)}이(가) 살해당했습니다. "
            f"역할은 ({role})였습니다.[/]"
        )
    elif kind == "night_safe":
        console.print("[bold blue]🌙 어젯밤은 아무도 죽지 않았습니다.[/]")


def run_demo(
    *,
    player_count: int,
    seed: int,
    client: Any,
    max_days: int = 20,
    console: Console | None = None,
) -> str:
    if console is None:
        console = Console(file=sys.stdout)

    rng = random.Random(seed)
    state = setup_game(player_count=player_count, rng=rng)
    actors: dict[str, PlayerInterface] = build_agents_for_state(state, client=client, rng=rng)
    jobs: dict[str, str] = {
        pid: a._persona.job for pid, a in actors.items() if hasattr(a, "_persona")
    }

    _print_setup(state, jobs, console)
    console.rule("[bold]Day 1 — 첫째 날 아침[/]")
    console.print("[dim]모두가 모였습니다. 자기소개부터 시작합니다... (LLM 호출 중)[/]")

    # Hook public_log so events stream live.
    day_ref = {"current": 1}
    state.public_log = _StreamingLog(
        on_append=lambda e: _print_event(state, e, console, day_ref, jobs)
    )

    winner = run_game(state, actors, max_days=max_days)

    # Show night kill summary (state.last_night_death is only the latest;
    # for retrospective deaths use player.alive flag against role table at end).
    console.rule("[bold red]GAME OVER[/]")
    if state.winner == Team.MAFIA:
        console.print("[bold red]마피아 승리![/]")
    elif state.winner == Team.CITIZEN:
        console.print("[bold green]시민 승리![/]")
    else:
        console.print(f"[yellow]게임 종료 ({winner})[/]")

    rows = []
    for p in state.players:
        job = jobs.get(p.id, "")
        label = f"{p.name}({job})" if job else p.name
        rows.append(f"  {p.id} {label}: {p.role.value} ({'생존' if p.alive else '사망'})")
    console.print(Panel("\n".join(rows), title="역할 공개", border_style="dim"))
    return winner


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="mafia-cli")
    parser.add_argument("--players", type=int, default=6, help="4~11")
    parser.add_argument("--seed", type=int, default=0)
    parser.add_argument("--max-days", type=int, default=20)
    args = parser.parse_args(argv)
    client = _make_client()
    console = Console(file=sys.stdout)
    try:
        run_demo(
            player_count=args.players,
            seed=args.seed,
            client=client,
            max_days=args.max_days,
            console=console,
        )
    except KeyboardInterrupt:
        console.print("\n[yellow]중단되었습니다.[/]")
        return 130
    return 0


if __name__ == "__main__":
    sys.exit(main())

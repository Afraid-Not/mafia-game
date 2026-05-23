"""Day phase: round-robin speeches and free-talk."""

from __future__ import annotations

from mafia.models import GameState
from mafia.player import DecisionContext, PlayerInterface


def run_day_roundrobin(
    state: GameState,
    actors: dict[str, PlayerInterface],
    passes: int = 1,
) -> None:
    """Every alive player speaks once per pass."""
    for pass_num in range(1, passes + 1):
        for player in state.alive_players():
            result = actors[player.id].decide(
                DecisionContext(state=state, actor_id=player.id, action="speak_turn")
            )
            state.public_log.append(
                {
                    "kind": "speak",
                    "speaker_id": player.id,
                    "text": result["text"],
                    "day_number": state.day_number,
                    "phase": "day_roundrobin",
                    "pass": pass_num,
                }
            )


def run_day_freetalk(
    state: GameState,
    actors: dict[str, PlayerInterface],
    max_rounds: int = 2,
    max_per_round: int = 3,
    min_eagerness: int = 3,
) -> None:
    """Each round, every alive player returns an eagerness score (cheap heuristic);
    up to `max_per_round` speakers with eagerness >= `min_eagerness` actually speak
    (LLM call). Default lets up to 3 people pile on each round and keeps quiet
    players from being forced to fill the air.
    """
    for _ in range(max_rounds):
        scored: list[tuple[int, str]] = []
        for player in state.alive_players():
            result = actors[player.id].decide(
                DecisionContext(state=state, actor_id=player.id, action="freetalk_eagerness")
            )
            scored.append((int(result["eagerness"]), player.id))
        scored.sort(reverse=True)

        winners = [(e, pid) for (e, pid) in scored[:max_per_round] if e >= min_eagerness]
        if not winners:
            # Nobody eager enough — skip this round entirely.
            continue

        for eagerness, speaker_id in winners:
            speech = actors[speaker_id].decide(
                DecisionContext(state=state, actor_id=speaker_id, action="speak_freetalk")
            )
            state.public_log.append(
                {
                    "kind": "speak_freetalk",
                    "speaker_id": speaker_id,
                    "text": speech["text"],
                    "eagerness": eagerness,
                    "day_number": state.day_number,
                }
            )

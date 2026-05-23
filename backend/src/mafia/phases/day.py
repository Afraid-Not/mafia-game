"""Day phase: round-robin speeches and free-talk."""
from __future__ import annotations

from mafia.models import GameState
from mafia.player import DecisionContext, PlayerInterface


def run_day_roundrobin(state: GameState, actors: dict[str, PlayerInterface]) -> None:
    """Every alive player speaks once. Order = stable list order (Phase 1)."""
    for player in state.alive_players():
        result = actors[player.id].decide(
            DecisionContext(state=state, actor_id=player.id, action="speak_turn")
        )
        state.public_log.append({
            "kind": "speak",
            "speaker_id": player.id,
            "text": result["text"],
            "day_number": state.day_number,
            "phase": "day_roundrobin",
        })


def run_day_freetalk(
    state: GameState,
    actors: dict[str, PlayerInterface],
    max_rounds: int = 2,
) -> None:
    """Each round, every alive player returns an eagerness score; the highest speaks."""
    for _ in range(max_rounds):
        scores: list[tuple[int, str, str]] = []  # (eagerness, speaker_id, text)
        for player in state.alive_players():
            result = actors[player.id].decide(
                DecisionContext(state=state, actor_id=player.id, action="speak_freetalk")
            )
            scores.append((int(result["eagerness"]), player.id, result["text"]))
        scores.sort(reverse=True)
        eagerness, speaker_id, text = scores[0]
        state.public_log.append({
            "kind": "speak_freetalk",
            "speaker_id": speaker_id,
            "text": text,
            "eagerness": eagerness,
            "day_number": state.day_number,
        })

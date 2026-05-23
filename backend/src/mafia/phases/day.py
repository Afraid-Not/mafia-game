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
        state.public_log.append(
            {
                "kind": "speak",
                "speaker_id": player.id,
                "text": result["text"],
                "day_number": state.day_number,
                "phase": "day_roundrobin",
            }
        )


def run_day_freetalk(
    state: GameState,
    actors: dict[str, PlayerInterface],
    max_rounds: int = 2,
) -> None:
    """Each round: ask every alive player for eagerness (cheap), let top speak (LLM)."""
    for _ in range(max_rounds):
        scored: list[tuple[int, str]] = []  # (eagerness, speaker_id)
        for player in state.alive_players():
            result = actors[player.id].decide(
                DecisionContext(state=state, actor_id=player.id, action="freetalk_eagerness")
            )
            scored.append((int(result["eagerness"]), player.id))
        scored.sort(reverse=True)
        eagerness, speaker_id = scored[0]
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

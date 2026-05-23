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

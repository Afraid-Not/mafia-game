"""Night phase: mafia kill, doctor protect, police investigate."""

from __future__ import annotations

from mafia.models import GameState, Player, Role
from mafia.player import DecisionContext, PlayerInterface


def _alive_mafia(state: GameState) -> list[Player]:
    return [p for p in state.alive_players() if p.role == Role.MAFIA]


def _decide_mafia_target_single(
    state: GameState, mafia: Player, actors: dict[str, PlayerInterface]
) -> str:
    ctx = DecisionContext(state=state, actor_id=mafia.id, action="night_kill")
    return actors[mafia.id].decide(ctx)["target_id"]


def run_night(state: GameState, actors: dict[str, PlayerInterface]) -> None:
    """Execute night actions and mutate `state` in place.

    Phase 1 scope: single-mafia kill with no doctor/police yet (extended in next tasks).
    """
    mafia = _alive_mafia(state)
    if not mafia:
        state.last_night_death = None
        return

    if len(mafia) == 1:
        target_id = _decide_mafia_target_single(state, mafia[0], actors)
    else:
        # extended in Task 9
        raise NotImplementedError("multi-mafia not implemented yet")

    # No doctor/police yet — extended in Tasks 10/11.
    target = state.player_by_id(target_id)
    target.alive = False
    state.last_night_death = target.id

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


def _decide_mafia_target_multi(
    state: GameState, mafia: list[Player], actors: dict[str, PlayerInterface]
) -> str:
    boss = next(m for m in mafia if m.is_mafia_boss)
    underlings = [m for m in mafia if not m.is_mafia_boss]

    propose = actors[boss.id].decide(
        DecisionContext(state=state, actor_id=boss.id, action="night_boss_propose")
    )
    proposed_target = propose["target_id"]
    state.mafia_log.append(
        {
            "speaker_id": boss.id,
            "text": propose.get("text", ""),
            "kind": "propose",
            "target_id": proposed_target,
        }
    )

    disagreements: list[Player] = []
    for u in underlings:
        resp = actors[u.id].decide(
            DecisionContext(
                state=state,
                actor_id=u.id,
                action="night_underling_respond",
                payload={"proposed_target_id": proposed_target},
            )
        )
        state.mafia_log.append(
            {
                "speaker_id": u.id,
                "text": resp.get("text", ""),
                "kind": "respond",
                "agree": resp["agree"],
            }
        )
        if resp["agree"] == "no":
            disagreements.append(u)

    if not disagreements:
        return proposed_target

    for d in disagreements:
        state.mafia_log.append({"speaker_id": d.id, "text": "(반대 표명)", "kind": "dissent"})

    final = actors[boss.id].decide(
        DecisionContext(
            state=state,
            actor_id=boss.id,
            action="night_boss_dialog",
            payload={
                "proposed_target_id": proposed_target,
                "dissenters": [d.id for d in disagreements],
            },
        )
    )
    state.mafia_log.append({"speaker_id": boss.id, "text": final.get("text", ""), "kind": "final"})
    final_target = final.get("final_target_id") or proposed_target
    return final_target


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
        target_id = _decide_mafia_target_multi(state, mafia, actors)

    # Doctor protection
    protected_id: str | None = None
    doctor = next((p for p in state.alive_players() if p.role == Role.DOCTOR), None)
    if doctor is not None:
        decision = actors[doctor.id].decide(
            DecisionContext(state=state, actor_id=doctor.id, action="night_doctor_protect")
        )
        protected_id = decision["target_id"]
        doctor.doctor_protections.append(protected_id)

    if protected_id == target_id:
        state.last_night_death = None
    else:
        target = state.player_by_id(target_id)
        target.alive = False
        state.last_night_death = target.id

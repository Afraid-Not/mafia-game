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
    max_rounds: int | None = None,
    max_per_round: int | None = None,
    min_eagerness: int = 3,
) -> None:
    """Each round, every alive player who has not yet spoken in this free-talk
    phase returns an eagerness score (cheap heuristic); up to `max_per_round`
    speakers with eagerness >= `min_eagerness` actually speak (LLM call). Each
    player speaks at most once across all rounds so we don't get the same agent
    re-stating themselves in a slightly different way.

    Day 1 uses tighter limits (round-robin precedes it); Day 2+ uses wider
    limits since freetalk is the only discussion mechanism. If no round
    produced any speaker, the single highest-eagerness player is forced to
    speak so the game never drops into vote with zero discussion.
    """
    if max_rounds is None:
        max_rounds = 2 if state.day_number == 1 else 3
    if max_per_round is None:
        max_per_round = 3 if state.day_number == 1 else 4

    spoken: set[str] = set()
    best_fallback: tuple[int, str] | None = None  # (eagerness, pid) for the no-winners guard

    for _ in range(max_rounds):
        scored: list[tuple[int, str]] = []
        for player in state.alive_players():
            if player.id in spoken:
                continue
            result = actors[player.id].decide(
                DecisionContext(state=state, actor_id=player.id, action="freetalk_eagerness")
            )
            scored.append((int(result["eagerness"]), player.id))
        scored.sort(reverse=True)

        if scored and (best_fallback is None or scored[0][0] > best_fallback[0]):
            best_fallback = scored[0]

        winners = [(e, pid) for (e, pid) in scored[:max_per_round] if e >= min_eagerness]
        if not winners:
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
            spoken.add(speaker_id)

    # Fallback (Day 2+ only — Day 1 already had round-robin intros).
    if state.day_number >= 2 and not spoken and best_fallback is not None:
        eagerness, speaker_id = best_fallback
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

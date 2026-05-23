"""Vote phase: nominate, last words, up/down."""

from __future__ import annotations

from collections import Counter

from mafia.models import GameState
from mafia.player import DecisionContext, PlayerInterface
from mafia.rules import vote_weight


def run_vote_nominate(state: GameState, actors: dict[str, PlayerInterface]) -> str | None:
    """Collect nominate votes; return the candidate id or None on tie / empty."""
    tally: Counter[str] = Counter()
    for voter in state.alive_players():
        decision = actors[voter.id].decide(
            DecisionContext(state=state, actor_id=voter.id, action="vote_nominate")
        )
        target_id = decision["target_id"]
        weight = vote_weight(state, voter.id)
        tally[target_id] += weight
        state.public_log.append(
            {
                "kind": "vote_nominate",
                "voter_id": voter.id,
                "target_id": target_id,
                "weight": weight,
            }
        )

    # Discard votes for dead or invalid targets
    alive_ids = {p.id for p in state.alive_players()}
    tally = Counter({t: c for t, c in tally.items() if t in alive_ids})

    if not tally:
        return None
    top_count = max(tally.values())
    top_targets = [t for t, c in tally.items() if c == top_count]
    if len(top_targets) > 1:
        return None
    return top_targets[0]


def run_last_words(
    state: GameState,
    actors: dict[str, PlayerInterface],
    candidate_id: str,
) -> None:
    decision = actors[candidate_id].decide(
        DecisionContext(state=state, actor_id=candidate_id, action="last_words")
    )
    state.public_log.append(
        {
            "kind": "last_words",
            "speaker_id": candidate_id,
            "text": decision["text"],
            "day_number": state.day_number,
        }
    )


def run_vote_updown(
    state: GameState,
    actors: dict[str, PlayerInterface],
    candidate_id: str,
) -> bool:
    """Each alive non-candidate votes yes/no. Yes-majority → execute.

    Returns True if the candidate was executed.
    """
    yes_count = 0
    no_count = 0
    for voter in state.alive_players():
        if voter.id == candidate_id:
            continue
        decision = actors[voter.id].decide(
            DecisionContext(
                state=state,
                actor_id=voter.id,
                action="vote_updown",
                payload={"candidate_id": candidate_id},
            )
        )
        weight = vote_weight(state, voter.id)
        if decision["vote"] == "yes":
            yes_count += weight
        else:
            no_count += weight
        state.public_log.append(
            {
                "kind": "vote_updown",
                "voter_id": voter.id,
                "vote": decision["vote"],
                "weight": weight,
                "candidate_id": candidate_id,
            }
        )

    executed = yes_count > no_count
    if executed:
        state.player_by_id(candidate_id).alive = False
        state.public_log.append(
            {
                "kind": "execution",
                "candidate_id": candidate_id,
                "yes": yes_count,
                "no": no_count,
            }
        )
    else:
        state.public_log.append(
            {
                "kind": "pardon",
                "candidate_id": candidate_id,
                "yes": yes_count,
                "no": no_count,
            }
        )
    return executed

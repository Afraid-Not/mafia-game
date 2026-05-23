"""Vote phase: nominate, last words, up/down."""
from __future__ import annotations

from collections import Counter

from mafia.models import GameState
from mafia.player import DecisionContext, PlayerInterface
from mafia.rules import vote_weight


def run_vote_nominate(
    state: GameState, actors: dict[str, PlayerInterface]
) -> str | None:
    """Collect nominate votes; return the candidate id or None on tie / empty."""
    tally: Counter[str] = Counter()
    for voter in state.alive_players():
        decision = actors[voter.id].decide(
            DecisionContext(state=state, actor_id=voter.id, action="vote_nominate")
        )
        target_id = decision["target_id"]
        weight = vote_weight(state, voter.id)
        tally[target_id] += weight
        state.public_log.append({
            "kind": "vote_nominate",
            "voter_id": voter.id,
            "target_id": target_id,
            "weight": weight,
        })

    if not tally:
        return None
    top_count = max(tally.values())
    top_targets = [t for t, c in tally.items() if c == top_count]
    if len(top_targets) > 1:
        return None
    return top_targets[0]

"""GameEngine: setup and state machine driver."""

from __future__ import annotations

import random

from mafia.models import GameState, Phase, Player, Role
from mafia.phases.day import run_day_freetalk, run_day_roundrobin
from mafia.phases.night import run_night
from mafia.phases.vote import run_last_words, run_vote_nominate, run_vote_updown
from mafia.player import PlayerInterface
from mafia.rules import check_winner, role_distribution


def setup_game(player_count: int, rng: random.Random) -> GameState:
    """Initialize a game: assign roles, designate mafia boss, set cleric_id."""
    roles = role_distribution(player_count)
    rng.shuffle(roles)

    players: list[Player] = []
    for i, role in enumerate(roles, start=1):
        players.append(Player(id=f"p{i}", name=f"Player{i}", role=role))

    mafia = [p for p in players if p.role == Role.MAFIA]
    if mafia:
        boss = rng.choice(mafia)
        boss.is_mafia_boss = True
        mafia_ids = [m.id for m in mafia]
        for m in mafia:
            m.known_mafia_ids = [mid for mid in mafia_ids if mid != m.id]

    cleric = next((p for p in players if p.role == Role.CLERIC), None)

    return GameState(
        players=players,
        day_number=1,
        phase=Phase.NIGHT,
        cleric_id=cleric.id if cleric else None,
    )


def run_game(
    state: GameState,
    actors: dict[str, PlayerInterface],
    max_days: int = 50,
) -> str:
    """Drive the state machine end-to-end. Returns the winning team name.

    Day-first ordering (classic Korean mafia): each iteration runs the day's
    discussion + voting first, then the night's mafia/doctor/police actions.
    On Day 1 the night has not yet happened, so the morning has no death to
    announce — players speak from a clean slate.
    """
    while state.day_number <= max_days:
        # DAY
        # Day 1 has round-robin intros + freetalk; later days are freetalk-only
        # because round-robin produces echo-chamber speeches when everyone shares
        # the same context. Freetalk lets agents react organically to one another.
        if state.day_number == 1:
            state.phase = Phase.DAY_ROUNDROBIN
            run_day_roundrobin(state, actors)

        state.phase = Phase.DAY_FREETALK
        run_day_freetalk(state, actors)

        # VOTE
        state.phase = Phase.VOTE_NOMINATE
        candidate_id = run_vote_nominate(state, actors)
        if candidate_id is not None:
            state.phase = Phase.LAST_WORDS
            run_last_words(state, actors, candidate_id)
            state.phase = Phase.VOTE_UPDOWN
            run_vote_updown(state, actors, candidate_id)

        winner = check_winner(state)
        if winner is not None:
            state.winner = winner
            state.phase = Phase.GAME_OVER
            return winner.value

        # NIGHT
        state.phase = Phase.NIGHT
        run_night(state, actors)
        winner = check_winner(state)
        if winner is not None:
            state.winner = winner
            state.phase = Phase.GAME_OVER
            return winner.value

        state.day_number += 1

    # Safety net
    state.phase = Phase.GAME_OVER
    return "draw"

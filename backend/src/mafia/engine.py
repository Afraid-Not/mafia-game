"""GameEngine: setup and state machine driver."""
from __future__ import annotations

import random

from mafia.models import GameState, Phase, Player, Role
from mafia.rules import role_distribution


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

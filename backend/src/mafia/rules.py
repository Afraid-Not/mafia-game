"""Game rules: role distribution and win conditions."""

from __future__ import annotations

from mafia.models import GameState, Role, Team

# (mafia, police, doctor, cleric) for player counts 4..11. Civilians fill the rest.
_DISTRIBUTION_TABLE: dict[int, tuple[int, int, int, int]] = {
    4: (1, 1, 0, 0),
    5: (1, 1, 0, 0),
    6: (2, 1, 1, 0),
    7: (2, 1, 1, 0),
    8: (3, 1, 1, 1),
    9: (3, 1, 1, 1),
    10: (4, 1, 1, 1),
    11: (4, 1, 1, 1),
}


def role_distribution(n: int) -> list[Role]:
    """Return a list of n roles for the given player count."""
    if n not in _DISTRIBUTION_TABLE:
        raise ValueError(f"player count {n} not supported (must be 4..11)")
    mafia, police, doctor, cleric = _DISTRIBUTION_TABLE[n]
    civilians = n - mafia - police - doctor - cleric
    roles: list[Role] = []
    roles.extend([Role.MAFIA] * mafia)
    roles.extend([Role.POLICE] * police)
    roles.extend([Role.DOCTOR] * doctor)
    roles.extend([Role.CLERIC] * cleric)
    roles.extend([Role.CIVILIAN] * civilians)
    return roles


def check_winner(state: GameState) -> Team | None:
    """Return the winning team if game is over, else None."""
    alive = state.alive_players()
    alive_mafia = [p for p in alive if p.role.team == Team.MAFIA]
    alive_citizens = [p for p in alive if p.role.team == Team.CITIZEN]
    if not alive_mafia:
        return Team.CITIZEN
    if len(alive_mafia) >= len(alive_citizens):
        return Team.MAFIA
    return None


def vote_weight(state: GameState, voter_id: str) -> int:
    """Vote weight for a given voter (2 for cleric, 1 otherwise)."""
    if state.cleric_id == voter_id:
        return 2
    return 1

from collections import Counter

import pytest

from mafia.models import GameState, Phase, Player, Role, Team
from mafia.rules import check_winner, role_distribution, vote_weight


@pytest.mark.parametrize(
    "n,expected",
    [
        (4, {Role.MAFIA: 1, Role.POLICE: 1, Role.CIVILIAN: 2}),
        (5, {Role.MAFIA: 1, Role.POLICE: 1, Role.CIVILIAN: 3}),
        (6, {Role.MAFIA: 2, Role.POLICE: 1, Role.DOCTOR: 1, Role.CIVILIAN: 2}),
        (7, {Role.MAFIA: 2, Role.POLICE: 1, Role.DOCTOR: 1, Role.CIVILIAN: 3}),
        (8, {Role.MAFIA: 3, Role.POLICE: 1, Role.DOCTOR: 1, Role.CLERIC: 1, Role.CIVILIAN: 2}),
        (9, {Role.MAFIA: 3, Role.POLICE: 1, Role.DOCTOR: 1, Role.CLERIC: 1, Role.CIVILIAN: 3}),
        (10, {Role.MAFIA: 4, Role.POLICE: 1, Role.DOCTOR: 1, Role.CLERIC: 1, Role.CIVILIAN: 3}),
        (11, {Role.MAFIA: 4, Role.POLICE: 1, Role.DOCTOR: 1, Role.CLERIC: 1, Role.CIVILIAN: 4}),
    ],
)
def test_role_distribution(n, expected):
    roles = role_distribution(n)
    assert len(roles) == n
    assert Counter(roles) == Counter(expected)


@pytest.mark.parametrize("n", [0, 1, 2, 3, 12, 100])
def test_role_distribution_out_of_range(n):
    with pytest.raises(ValueError):
        role_distribution(n)


def _state(players: list[Player], cleric_id: str | None = None) -> GameState:
    return GameState(players=players, day_number=0, phase=Phase.LOBBY, cleric_id=cleric_id)


def test_check_winner_citizens_when_all_mafia_dead():
    players = [
        Player(id="p1", name="A", role=Role.MAFIA, alive=False),
        Player(id="p2", name="B", role=Role.CIVILIAN, alive=True),
        Player(id="p3", name="C", role=Role.CIVILIAN, alive=True),
    ]
    assert check_winner(_state(players)) == Team.CITIZEN


def test_check_winner_mafia_when_parity():
    players = [
        Player(id="p1", name="A", role=Role.MAFIA, alive=True),
        Player(id="p2", name="B", role=Role.CIVILIAN, alive=True),
    ]
    assert check_winner(_state(players)) == Team.MAFIA


def test_check_winner_mafia_when_majority():
    players = [
        Player(id="p1", name="A", role=Role.MAFIA, alive=True),
        Player(id="p2", name="B", role=Role.MAFIA, alive=True),
        Player(id="p3", name="C", role=Role.CIVILIAN, alive=True),
    ]
    assert check_winner(_state(players)) == Team.MAFIA


def test_check_winner_none_when_game_active():
    players = [
        Player(id="p1", name="A", role=Role.MAFIA, alive=True),
        Player(id="p2", name="B", role=Role.CIVILIAN, alive=True),
        Player(id="p3", name="C", role=Role.CIVILIAN, alive=True),
    ]
    assert check_winner(_state(players)) is None


def test_vote_weight_cleric_is_two():
    players = [Player(id="p1", name="A", role=Role.CLERIC)]
    state = _state(players, cleric_id="p1")
    assert vote_weight(state, "p1") == 2


def test_vote_weight_non_cleric_is_one():
    players = [Player(id="p1", name="A", role=Role.CIVILIAN)]
    state = _state(players, cleric_id=None)
    assert vote_weight(state, "p1") == 1

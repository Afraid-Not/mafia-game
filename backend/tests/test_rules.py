from collections import Counter

import pytest

from mafia.models import Role
from mafia.rules import role_distribution


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

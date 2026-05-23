import random

import pytest

from mafia.engine import setup_game
from mafia.models import Phase, Role


def test_setup_game_assigns_correct_roles_for_6_players():
    state = setup_game(player_count=6, rng=random.Random(42))
    role_counts = {r: 0 for r in Role}
    for p in state.players:
        role_counts[p.role] += 1
    assert role_counts[Role.MAFIA] == 2
    assert role_counts[Role.POLICE] == 1
    assert role_counts[Role.DOCTOR] == 1
    assert role_counts[Role.CIVILIAN] == 2
    assert role_counts[Role.CLERIC] == 0


def test_setup_game_designates_one_mafia_boss():
    state = setup_game(player_count=8, rng=random.Random(1))
    mafia = [p for p in state.players if p.role == Role.MAFIA]
    bosses = [m for m in mafia if m.is_mafia_boss]
    assert len(bosses) == 1


def test_setup_game_known_mafia_ids_populated_for_each_mafia():
    state = setup_game(player_count=6, rng=random.Random(1))
    mafia_ids = sorted(p.id for p in state.players if p.role == Role.MAFIA)
    for m in state.players:
        if m.role == Role.MAFIA:
            assert sorted(m.known_mafia_ids) == [mid for mid in mafia_ids if mid != m.id]


def test_setup_game_sets_cleric_id_when_present():
    state = setup_game(player_count=8, rng=random.Random(1))
    cleric = next(p for p in state.players if p.role == Role.CLERIC)
    assert state.cleric_id == cleric.id


def test_setup_game_initial_phase_is_night():
    state = setup_game(player_count=4, rng=random.Random(1))
    assert state.phase == Phase.NIGHT
    assert state.day_number == 1


def test_setup_game_invalid_count_raises():
    with pytest.raises(ValueError):
        setup_game(player_count=3, rng=random.Random(0))

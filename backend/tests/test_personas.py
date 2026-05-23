import random

import pytest

from mafia.agents.personas import load_personas


def test_load_personas_returns_50():
    pool = load_personas()
    assert len(pool.all_personas) == 50


def test_personas_have_required_fields():
    pool = load_personas()
    for p in pool.all_personas:
        assert isinstance(p.id, int)
        assert isinstance(p.name, str) and p.name
        assert isinstance(p.job, str) and p.job
        assert isinstance(p.personality, str) and p.personality
        assert isinstance(p.style, str) and p.style


def test_persona_names_unique():
    pool = load_personas()
    names = [p.name for p in pool.all_personas]
    assert len(set(names)) == 50


def test_draw_returns_distinct_personas():
    pool = load_personas()
    drawn = pool.draw(8, rng=random.Random(42))
    assert len(drawn) == 8
    assert len({p.id for p in drawn}) == 8


def test_draw_deterministic_with_same_rng():
    pool = load_personas()
    drawn1 = pool.draw(6, rng=random.Random(7))
    drawn2 = pool.draw(6, rng=random.Random(7))
    assert [p.id for p in drawn1] == [p.id for p in drawn2]


def test_draw_too_many_raises():
    pool = load_personas()
    with pytest.raises(ValueError):
        pool.draw(51, rng=random.Random(0))

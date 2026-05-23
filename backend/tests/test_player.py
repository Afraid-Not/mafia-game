import pytest

from mafia.models import GameState, Phase
from mafia.player import DecisionContext, MockPlayer


def _ctx(state: GameState, actor_id: str, action: str, **payload) -> DecisionContext:
    return DecisionContext(state=state, actor_id=actor_id, action=action, payload=payload)


def test_mock_speak_turn_returns_canned_text():
    p = MockPlayer(scripted={"speak_turn": "I am a citizen"})
    ctx = _ctx(GameState(players=[], day_number=1, phase=Phase.DAY_ROUNDROBIN), "p1", "speak_turn")
    out = p.decide(ctx)
    assert out == {"text": "I am a citizen"}


def test_mock_vote_nominate_returns_target():
    p = MockPlayer(scripted={"vote_nominate": "p2"})
    ctx = _ctx(
        GameState(players=[], day_number=1, phase=Phase.VOTE_NOMINATE), "p1", "vote_nominate"
    )
    out = p.decide(ctx)
    assert out == {"target_id": "p2", "reasoning": "mock"}


def test_mock_freetalk_eagerness_and_text():
    p = MockPlayer(scripted={"speak_freetalk": {"eagerness": 7, "text": "hmm"}})
    ctx = _ctx(
        GameState(players=[], day_number=1, phase=Phase.DAY_FREETALK), "p1", "speak_freetalk"
    )
    out = p.decide(ctx)
    assert out == {"eagerness": 7, "text": "hmm"}


def test_mock_missing_action_raises():
    p = MockPlayer(scripted={})
    ctx = _ctx(GameState(players=[], day_number=1, phase=Phase.NIGHT), "p1", "night_kill")
    with pytest.raises(KeyError):
        p.decide(ctx)

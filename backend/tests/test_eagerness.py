from mafia.agents.eagerness import compute_eagerness
from mafia.models import GameState, Phase, Player, Role


def _state_with_log(speakers_in_order: list[str], extra_log: list[dict] | None = None) -> GameState:
    players = [Player(id=pid, name=pid, role=Role.CIVILIAN) for pid in {"p1", "p2", "p3"}]
    state = GameState(players=players, day_number=1, phase=Phase.DAY_FREETALK)
    for s in speakers_in_order:
        state.public_log.append(
            {"kind": "speak", "speaker_id": s, "text": f"hello from {s}", "day_number": 1}
        )
    if extra_log:
        state.public_log.extend(extra_log)
    return state


def test_eagerness_zero_baseline():
    state = _state_with_log([])
    score = compute_eagerness(state, actor_id="p1")
    assert score >= 0


def test_eagerness_increases_when_name_mentioned():
    state = _state_with_log([])
    state.public_log.append(
        {"kind": "speak", "speaker_id": "p2", "text": "p1 이상해", "day_number": 1}
    )
    score_mentioned = compute_eagerness(state, actor_id="p1")
    state2 = _state_with_log([])
    state2.public_log.append(
        {"kind": "speak", "speaker_id": "p2", "text": "그냥 평범한 발언", "day_number": 1}
    )
    score_not_mentioned = compute_eagerness(state2, actor_id="p1")
    assert score_mentioned > score_not_mentioned


def test_eagerness_increases_with_silence():
    # p1 spoke long ago; p2 spoke recently
    state = _state_with_log(["p1", "p2", "p3", "p2", "p3"])
    score_p1 = compute_eagerness(state, actor_id="p1")
    score_p2 = compute_eagerness(state, actor_id="p2")
    assert score_p1 > score_p2


def test_eagerness_bonus_when_voted_against():
    state = _state_with_log([])
    state.public_log.append(
        {"kind": "vote_nominate", "voter_id": "p2", "target_id": "p1", "weight": 1}
    )
    state.public_log.append(
        {"kind": "vote_nominate", "voter_id": "p3", "target_id": "p1", "weight": 1}
    )
    score = compute_eagerness(state, actor_id="p1")
    # Must include the votes-against bonus
    assert score >= 4  # 2 votes × 2 weight per nomination + silence bonus etc.


def test_eagerness_clamped_to_non_negative():
    state = _state_with_log([])
    score = compute_eagerness(state, actor_id="p_unknown")
    assert score >= 0

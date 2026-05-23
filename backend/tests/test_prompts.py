from mafia.agents.personas import Persona
from mafia.agents.prompts import (
    build_system_prompt,
    build_user_prompt,
)
from mafia.models import GameState, Phase, Player, Role

_PERSONA = Persona(id=1, name="Tom", job="탐정", personality="의심많음", style="잠깐만요")


def _state(actor_role: Role = Role.CIVILIAN) -> tuple[GameState, Player]:
    players = [
        Player(id="p1", name="Tom", role=actor_role),
        Player(id="p2", name="John", role=Role.CIVILIAN),
        Player(id="p3", name="Sara", role=Role.MAFIA, is_mafia_boss=True, known_mafia_ids=["p4"]),
        Player(id="p4", name="Mike", role=Role.MAFIA, known_mafia_ids=["p3"]),
    ]
    state = GameState(players=players, day_number=2, phase=Phase.DAY_ROUNDROBIN)
    actor = players[0]
    return state, actor


def test_system_prompt_includes_persona_fields():
    state, actor = _state()
    sys_text = build_system_prompt(state=state, actor=actor, persona=_PERSONA)
    assert "Tom" in sys_text
    assert "탐정" in sys_text
    assert "의심많음" in sys_text
    assert "잠깐만요" in sys_text
    # Role label present in some form
    assert "시민" in sys_text or "civilian" in sys_text.lower()


def test_system_prompt_includes_mafia_allies_when_mafia():
    state, _ = _state(actor_role=Role.MAFIA)
    state.players[0].known_mafia_ids = ["p3", "p4"]
    sys_text = build_system_prompt(state=state, actor=state.players[0], persona=_PERSONA)
    assert "Sara" in sys_text or "p3" in sys_text
    assert "Mike" in sys_text or "p4" in sys_text


def test_user_prompt_speak_turn_includes_recent_log():
    state, actor = _state()
    state.public_log.append({"kind": "speak", "speaker_id": "p2", "text": "안녕", "day_number": 2})
    user_text = build_user_prompt(state=state, actor=actor, action="speak_turn", payload={})
    assert "John" in user_text or "p2" in user_text
    assert "안녕" in user_text
    assert "speak_turn" in user_text or "발언" in user_text


def test_user_prompt_vote_nominate_lists_candidates():
    state, actor = _state()
    user_text = build_user_prompt(state=state, actor=actor, action="vote_nominate", payload={})
    # All alive players except self should be listed as candidates
    for pid in ["John", "Sara", "Mike"]:
        assert pid in user_text
    assert "target_id" in user_text  # JSON schema hint


def test_user_prompt_vote_updown_requires_yes_or_no():
    state, actor = _state()
    user_text = build_user_prompt(
        state=state, actor=actor, action="vote_updown", payload={"candidate_id": "p3"}
    )
    assert "Sara" in user_text or "p3" in user_text
    assert "yes" in user_text and "no" in user_text

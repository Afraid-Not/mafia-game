from unittest.mock import MagicMock

from mafia.agents.llm_agent import LLMAgent
from mafia.agents.personas import Persona
from mafia.models import GameState, Phase, Player, Role
from mafia.player import DecisionContext

_PERSONA = Persona(id=1, name="Tom", job="탐정", personality="의심", style="잠깐만요")


def _state_and_actor():
    players = [
        Player(id="p1", name="Tom", role=Role.CIVILIAN),
        Player(id="p2", name="John", role=Role.MAFIA, is_mafia_boss=True),
        Player(id="p3", name="Sara", role=Role.CIVILIAN),
    ]
    state = GameState(players=players, day_number=1, phase=Phase.DAY_ROUNDROBIN)
    return state, players[0]


def test_speak_turn_calls_llm_text_mode():
    state, actor = _state_and_actor()
    client = MagicMock()
    client.complete_json.return_value = {"text": "이상한 분위기야"}
    agent = LLMAgent(actor=actor, persona=_PERSONA, client=client)

    out = agent.decide(DecisionContext(state=state, actor_id=actor.id, action="speak_turn"))
    assert out == {"text": "이상한 분위기야"}
    client.complete_json.assert_called_once()  # speak_turn uses JSON mode for consistency


def test_freetalk_eagerness_uses_heuristic_no_llm():
    state, actor = _state_and_actor()
    client = MagicMock()
    agent = LLMAgent(actor=actor, persona=_PERSONA, client=client)

    out = agent.decide(DecisionContext(state=state, actor_id=actor.id, action="freetalk_eagerness"))
    assert "eagerness" in out
    assert isinstance(out["eagerness"], int)
    client.complete.assert_not_called()
    client.complete_json.assert_not_called()


def test_vote_nominate_parses_target_and_reasoning():
    state, actor = _state_and_actor()
    client = MagicMock()
    client.complete_json.return_value = {"target_id": "p2", "reasoning": "수상해"}
    agent = LLMAgent(actor=actor, persona=_PERSONA, client=client)

    out = agent.decide(DecisionContext(state=state, actor_id=actor.id, action="vote_nominate"))
    assert out["target_id"] == "p2"
    assert "reasoning" in out


def test_invalid_target_falls_back_to_first_candidate():
    state, actor = _state_and_actor()
    client = MagicMock()
    # LLM returns a dead/invalid target
    client.complete_json.return_value = {"target_id": "p_nonexistent", "reasoning": "?"}
    agent = LLMAgent(actor=actor, persona=_PERSONA, client=client)

    out = agent.decide(DecisionContext(state=state, actor_id=actor.id, action="vote_nominate"))
    # Should snap to an alive non-self id
    assert out["target_id"] in {"p2", "p3"}


def test_system_prompt_built_once_per_action_call():
    # Sanity: complete_json receives the persona name in `system` arg.
    state, actor = _state_and_actor()
    client = MagicMock()
    client.complete_json.return_value = {"text": "안녕"}
    agent = LLMAgent(actor=actor, persona=_PERSONA, client=client)
    agent.decide(DecisionContext(state=state, actor_id=actor.id, action="speak_turn"))
    sys_arg = client.complete_json.call_args.kwargs["system"]
    assert "Tom" in sys_arg

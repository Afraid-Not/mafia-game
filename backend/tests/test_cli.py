from unittest.mock import MagicMock

from mafia.cli import build_agents_for_state, main, run_demo
from mafia.engine import setup_game


def test_build_agents_for_state_assigns_distinct_personas():
    import random

    state = setup_game(player_count=6, rng=random.Random(123))
    fake_client = MagicMock()
    agents = build_agents_for_state(state, client=fake_client, rng=random.Random(123))
    assert set(agents.keys()) == {p.id for p in state.players}
    persona_ids = [a._persona.id for a in agents.values()]  # noqa: SLF001
    assert len(set(persona_ids)) == 6


def test_run_demo_uses_mock_actors_and_prints(capsys):
    # Use a stub client whose complete_json always returns reasonable shapes
    fake_client = MagicMock()
    fake_client.complete_json.side_effect = _stub_complete_json
    run_demo(player_count=4, seed=99, client=fake_client, max_days=5)
    captured = capsys.readouterr()
    assert "Day" in captured.out
    assert "GAME OVER" in captured.out.upper() or "게임 종료" in captured.out


def _stub_complete_json(*, system: str, user: str):
    # Decide what to return based on the user prompt content
    if "speak_turn" in user or "발언 (1~3문장)" in user or "발언" in user and "자유" not in user:
        return {"text": "흠..."}
    if "자유발언" in user or "speak_freetalk" in user:
        return {"text": "..."}
    if "찬반" in user or "vote_updown" in user:
        return {"vote": "yes", "reasoning": "ok"}
    if "지명" in user or "vote_nominate" in user:
        return {"target_id": "p2", "reasoning": "ok"}
    if "타겟" in user or "night_kill" in user or "두목" in user:
        return {"target_id": "p1", "reasoning": "ok", "text": "p1로"}
    if "동의" in user or "night_underling_respond" in user:
        return {"agree": "yes", "reasoning": "ok", "text": "ok"}
    if "최종" in user or "night_boss_dialog" in user:
        return {"text": "확정", "final_target_id": None}
    if "보호" in user or "night_doctor_protect" in user:
        return {"target_id": "p1", "reasoning": "ok"}
    if "조사" in user or "night_police_investigate" in user:
        return {"target_id": "p1", "reasoning": "ok"}
    if "최후" in user or "last_words" in user:
        return {"text": "억울합니다"}
    return {"text": "..."}


def test_main_with_args(monkeypatch, capsys):
    fake_client = MagicMock()
    fake_client.complete_json.side_effect = _stub_complete_json
    monkeypatch.setattr("mafia.cli._make_client", lambda: fake_client)
    rc = main(["--players", "4", "--seed", "7", "--max-days", "5"])
    assert rc == 0

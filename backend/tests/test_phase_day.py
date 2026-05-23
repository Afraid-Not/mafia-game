from mafia.models import GameState, Phase, Player, Role
from mafia.phases.day import run_day_freetalk, run_day_roundrobin
from mafia.player import MockPlayer


def test_roundrobin_collects_one_speech_per_alive_player():
    players = [
        Player(id="p1", name="A", role=Role.CIVILIAN),
        Player(id="p2", name="B", role=Role.MAFIA, is_mafia_boss=True),
        Player(id="p3", name="C", role=Role.CIVILIAN, alive=False),
    ]
    state = GameState(players=players, day_number=1, phase=Phase.DAY_ROUNDROBIN)
    actors = {
        "p1": MockPlayer({"speak_turn": "안녕"}),
        "p2": MockPlayer({"speak_turn": "흠"}),
        "p3": MockPlayer({}),
    }
    run_day_roundrobin(state, actors)
    speeches = [e for e in state.public_log if e["kind"] == "speak"]
    speakers = [s["speaker_id"] for s in speeches]
    assert sorted(speakers) == ["p1", "p2"]
    assert "p3" not in speakers


def test_freetalk_uses_eagerness_check_then_speaks_only_winner():
    players = [
        Player(id="p1", name="A", role=Role.CIVILIAN),
        Player(id="p2", name="B", role=Role.CIVILIAN),
        Player(id="p3", name="C", role=Role.CIVILIAN),
    ]
    state = GameState(players=players, day_number=1, phase=Phase.DAY_FREETALK)
    actors = {
        "p1": MockPlayer({"freetalk_eagerness": 9, "speak_freetalk": "say9"}),
        "p2": MockPlayer({"freetalk_eagerness": 5, "speak_freetalk": "say5"}),
        "p3": MockPlayer({"freetalk_eagerness": 1, "speak_freetalk": "say1"}),
    }
    run_day_freetalk(state, actors, max_rounds=2)
    speeches = [e for e in state.public_log if e["kind"] == "speak_freetalk"]
    assert len(speeches) == 2
    assert all(s["speaker_id"] == "p1" for s in speeches)
    assert all(s["text"] == "say9" for s in speeches)

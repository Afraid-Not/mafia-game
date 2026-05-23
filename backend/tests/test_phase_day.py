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


def test_freetalk_picks_highest_eagerness_per_round_max_2_rounds():
    players = [
        Player(id="p1", name="A", role=Role.CIVILIAN),
        Player(id="p2", name="B", role=Role.CIVILIAN),
        Player(id="p3", name="C", role=Role.CIVILIAN),
    ]
    state = GameState(players=players, day_number=1, phase=Phase.DAY_FREETALK)
    actors = {
        "p1": MockPlayer({"speak_freetalk": {"eagerness": 9, "text": "say9"}}),
        "p2": MockPlayer({"speak_freetalk": {"eagerness": 5, "text": "say5"}}),
        "p3": MockPlayer({"speak_freetalk": {"eagerness": 1, "text": "say1"}}),
    }
    run_day_freetalk(state, actors, max_rounds=2)
    speeches = [e for e in state.public_log if e["kind"] == "speak_freetalk"]
    # 2 rounds * 1 speaker per round = 2 entries, both from p1
    assert len(speeches) == 2
    assert all(s["speaker_id"] == "p1" for s in speeches)

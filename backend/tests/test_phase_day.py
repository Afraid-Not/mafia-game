from mafia.models import GameState, Phase, Player, Role
from mafia.phases.day import run_day_freetalk, run_day_roundrobin
from mafia.player import MockPlayer


def test_roundrobin_each_alive_player_speaks_twice_by_default():
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
    # 2 passes × 2 alive players = 4 speeches; dead p3 never speaks
    assert sorted(speakers) == ["p1", "p1", "p2", "p2"]
    assert "p3" not in speakers


def test_roundrobin_respects_passes_argument():
    players = [Player(id="p1", name="A", role=Role.CIVILIAN)]
    state = GameState(players=players, day_number=1, phase=Phase.DAY_ROUNDROBIN)
    actors = {"p1": MockPlayer({"speak_turn": "ok"})}
    run_day_roundrobin(state, actors, passes=3)
    speeches = [e for e in state.public_log if e["kind"] == "speak"]
    assert len(speeches) == 3


def test_freetalk_top_eager_within_threshold_speak():
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
    run_day_freetalk(state, actors, max_rounds=1, max_per_round=3, min_eagerness=3)
    speeches = [e for e in state.public_log if e["kind"] == "speak_freetalk"]
    speaker_ids = [s["speaker_id"] for s in speeches]
    assert sorted(speaker_ids) == ["p1", "p2"]  # p3 below threshold


def test_freetalk_caps_speakers_per_round_to_max():
    players = [
        Player(id="p1", name="A", role=Role.CIVILIAN),
        Player(id="p2", name="B", role=Role.CIVILIAN),
        Player(id="p3", name="C", role=Role.CIVILIAN),
        Player(id="p4", name="D", role=Role.CIVILIAN),
    ]
    state = GameState(players=players, day_number=1, phase=Phase.DAY_FREETALK)
    actors = {
        "p1": MockPlayer({"freetalk_eagerness": 9, "speak_freetalk": "s1"}),
        "p2": MockPlayer({"freetalk_eagerness": 8, "speak_freetalk": "s2"}),
        "p3": MockPlayer({"freetalk_eagerness": 7, "speak_freetalk": "s3"}),
        "p4": MockPlayer({"freetalk_eagerness": 6, "speak_freetalk": "s4"}),
    }
    run_day_freetalk(state, actors, max_rounds=1, max_per_round=2, min_eagerness=0)
    speeches = [e for e in state.public_log if e["kind"] == "speak_freetalk"]
    assert len(speeches) == 2
    assert sorted([s["speaker_id"] for s in speeches]) == ["p1", "p2"]


def test_freetalk_skips_round_when_nobody_eager_enough():
    players = [
        Player(id="p1", name="A", role=Role.CIVILIAN),
        Player(id="p2", name="B", role=Role.CIVILIAN),
    ]
    state = GameState(players=players, day_number=1, phase=Phase.DAY_FREETALK)
    actors = {
        "p1": MockPlayer({"freetalk_eagerness": 1, "speak_freetalk": "skip1"}),
        "p2": MockPlayer({"freetalk_eagerness": 2, "speak_freetalk": "skip2"}),
    }
    run_day_freetalk(state, actors, max_rounds=2, min_eagerness=5)
    speeches = [e for e in state.public_log if e["kind"] == "speak_freetalk"]
    assert speeches == []

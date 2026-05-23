from mafia.models import GameState, Phase, Player, Role
from mafia.phases.night import run_night
from mafia.player import MockPlayer


def test_single_mafia_kills_target_no_doctor():
    players = [
        Player(id="m1", name="M", role=Role.MAFIA, is_mafia_boss=True),
        Player(id="c1", name="A", role=Role.CIVILIAN),
        Player(id="c2", name="B", role=Role.CIVILIAN),
    ]
    state = GameState(players=players, day_number=0, phase=Phase.NIGHT)
    actors = {
        "m1": MockPlayer({"night_kill": "c1"}),
        "c1": MockPlayer({}),
        "c2": MockPlayer({}),
    }
    run_night(state, actors)
    assert state.player_by_id("c1").alive is False
    assert state.last_night_death == "c1"
    assert state.player_by_id("c2").alive is True


def test_multi_mafia_all_agree_kills_proposed_target():
    players = [
        Player(id="m1", name="Boss", role=Role.MAFIA, is_mafia_boss=True,
               known_mafia_ids=["m2"]),
        Player(id="m2", name="Underling", role=Role.MAFIA, known_mafia_ids=["m1"]),
        Player(id="c1", name="A", role=Role.CIVILIAN),
        Player(id="c2", name="B", role=Role.CIVILIAN),
    ]
    state = GameState(players=players, day_number=0, phase=Phase.NIGHT)
    actors = {
        "m1": MockPlayer({"night_boss_propose": "c1"}),
        "m2": MockPlayer({"night_underling_respond": "yes"}),
        "c1": MockPlayer({}),
        "c2": MockPlayer({}),
    }
    run_night(state, actors)
    assert state.player_by_id("c1").alive is False
    assert state.last_night_death == "c1"


def test_multi_mafia_underling_disagrees_boss_overrides():
    players = [
        Player(id="m1", name="Boss", role=Role.MAFIA, is_mafia_boss=True,
               known_mafia_ids=["m2"]),
        Player(id="m2", name="Underling", role=Role.MAFIA, known_mafia_ids=["m1"]),
        Player(id="c1", name="A", role=Role.CIVILIAN),
        Player(id="c2", name="B", role=Role.CIVILIAN),
    ]
    state = GameState(players=players, day_number=0, phase=Phase.NIGHT)
    actors = {
        "m1": MockPlayer({
            "night_boss_propose": "c1",
            "night_boss_dialog": {"text": "그래도 c1이야", "final_target_id": "c1"},
        }),
        "m2": MockPlayer({"night_underling_respond": {
            "agree": "no", "reasoning": "c2가 더 의심", "text": "c2가 어때?"
        }}),
        "c1": MockPlayer({}),
        "c2": MockPlayer({}),
    }
    run_night(state, actors)
    assert state.last_night_death == "c1"


def test_multi_mafia_underling_disagrees_boss_changes_mind():
    players = [
        Player(id="m1", name="Boss", role=Role.MAFIA, is_mafia_boss=True,
               known_mafia_ids=["m2"]),
        Player(id="m2", name="Underling", role=Role.MAFIA, known_mafia_ids=["m1"]),
        Player(id="c1", name="A", role=Role.CIVILIAN),
        Player(id="c2", name="B", role=Role.CIVILIAN),
    ]
    state = GameState(players=players, day_number=0, phase=Phase.NIGHT)
    actors = {
        "m1": MockPlayer({
            "night_boss_propose": "c1",
            "night_boss_dialog": {"text": "좋아 c2로", "final_target_id": "c2"},
        }),
        "m2": MockPlayer({"night_underling_respond": {
            "agree": "no", "reasoning": "c2", "text": "c2가 더 의심"
        }}),
        "c1": MockPlayer({}),
        "c2": MockPlayer({}),
    }
    run_night(state, actors)
    assert state.last_night_death == "c2"


def test_doctor_protects_mafia_target_survives():
    players = [
        Player(id="m1", name="M", role=Role.MAFIA, is_mafia_boss=True),
        Player(id="d1", name="Doc", role=Role.DOCTOR),
        Player(id="c1", name="A", role=Role.CIVILIAN),
    ]
    state = GameState(players=players, day_number=0, phase=Phase.NIGHT)
    actors = {
        "m1": MockPlayer({"night_kill": "c1"}),
        "d1": MockPlayer({"night_doctor_protect": "c1"}),
        "c1": MockPlayer({}),
    }
    run_night(state, actors)
    assert state.player_by_id("c1").alive is True
    assert state.last_night_death is None


def test_doctor_protects_someone_else_target_dies():
    players = [
        Player(id="m1", name="M", role=Role.MAFIA, is_mafia_boss=True),
        Player(id="d1", name="Doc", role=Role.DOCTOR),
        Player(id="c1", name="A", role=Role.CIVILIAN),
    ]
    state = GameState(players=players, day_number=0, phase=Phase.NIGHT)
    actors = {
        "m1": MockPlayer({"night_kill": "c1"}),
        "d1": MockPlayer({"night_doctor_protect": "d1"}),  # self-protect
        "c1": MockPlayer({}),
    }
    run_night(state, actors)
    assert state.player_by_id("c1").alive is False
    assert state.last_night_death == "c1"


def test_police_investigates_mafia_records_true():
    players = [
        Player(id="m1", name="M", role=Role.MAFIA, is_mafia_boss=True),
        Player(id="p1", name="Cop", role=Role.POLICE),
        Player(id="c1", name="A", role=Role.CIVILIAN),
    ]
    state = GameState(players=players, day_number=0, phase=Phase.NIGHT)
    actors = {
        "m1": MockPlayer({"night_kill": "c1"}),
        "p1": MockPlayer({"night_police_investigate": "m1"}),
        "c1": MockPlayer({}),
    }
    run_night(state, actors)
    cop = state.player_by_id("p1")
    assert cop.police_investigations == [("m1", True)]


def test_police_investigates_citizen_records_false():
    players = [
        Player(id="m1", name="M", role=Role.MAFIA, is_mafia_boss=True),
        Player(id="p1", name="Cop", role=Role.POLICE),
        Player(id="c1", name="A", role=Role.CIVILIAN),
    ]
    state = GameState(players=players, day_number=0, phase=Phase.NIGHT)
    actors = {
        "m1": MockPlayer({"night_kill": "c1"}),
        "p1": MockPlayer({"night_police_investigate": "c1"}),
        "c1": MockPlayer({}),
    }
    run_night(state, actors)
    cop = state.player_by_id("p1")
    assert cop.police_investigations == [("c1", False)]

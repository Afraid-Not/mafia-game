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

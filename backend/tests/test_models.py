from mafia.models import GameState, Phase, Player, Role, Team


def test_roles_have_team_attribute():
    assert Role.MAFIA.team == Team.MAFIA
    assert Role.CIVILIAN.team == Team.CITIZEN
    assert Role.POLICE.team == Team.CITIZEN
    assert Role.DOCTOR.team == Team.CITIZEN
    assert Role.CLERIC.team == Team.CITIZEN


def test_phases_exist():
    assert Phase.LOBBY
    assert Phase.NIGHT
    assert Phase.DAY_ROUNDROBIN
    assert Phase.DAY_FREETALK
    assert Phase.VOTE_NOMINATE
    assert Phase.LAST_WORDS
    assert Phase.VOTE_UPDOWN
    assert Phase.CHECK_WIN
    assert Phase.GAME_OVER


def test_player_construction():
    p = Player(id="p1", name="Tom", role=Role.MAFIA, is_mafia_boss=True)
    assert p.id == "p1"
    assert p.role == Role.MAFIA
    assert p.alive is True
    assert p.is_mafia_boss is True


def test_player_default_alive_true():
    p = Player(id="p2", name="Sarah", role=Role.CIVILIAN)
    assert p.alive is True
    assert p.is_mafia_boss is False


def test_gamestate_construction():
    players = [
        Player(id="p1", name="Tom", role=Role.MAFIA, is_mafia_boss=True),
        Player(id="p2", name="Sarah", role=Role.CIVILIAN),
    ]
    state = GameState(players=players, day_number=0, phase=Phase.LOBBY)
    assert state.day_number == 0
    assert state.phase == Phase.LOBBY
    assert state.alive_players() == players


def test_gamestate_alive_filter():
    players = [
        Player(id="p1", name="A", role=Role.CIVILIAN, alive=True),
        Player(id="p2", name="B", role=Role.MAFIA, alive=False),
    ]
    state = GameState(players=players, day_number=1, phase=Phase.DAY_ROUNDROBIN)
    assert len(state.alive_players()) == 1
    assert state.alive_players()[0].id == "p1"


def test_gamestate_player_by_id():
    players = [Player(id="p1", name="A", role=Role.CIVILIAN)]
    state = GameState(players=players, day_number=0, phase=Phase.LOBBY)
    assert state.player_by_id("p1").name == "A"

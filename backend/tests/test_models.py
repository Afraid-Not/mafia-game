from mafia.models import Role, Phase, Team


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

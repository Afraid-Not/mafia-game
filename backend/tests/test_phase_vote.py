from mafia.models import GameState, Phase, Player, Role
from mafia.phases.vote import run_vote_nominate
from mafia.player import MockPlayer


def test_nominate_majority_wins():
    players = [
        Player(id="p1", name="A", role=Role.CIVILIAN),
        Player(id="p2", name="B", role=Role.CIVILIAN),
        Player(id="p3", name="C", role=Role.MAFIA, is_mafia_boss=True),
    ]
    state = GameState(players=players, day_number=1, phase=Phase.VOTE_NOMINATE)
    actors = {
        "p1": MockPlayer({"vote_nominate": "p3"}),
        "p2": MockPlayer({"vote_nominate": "p3"}),
        "p3": MockPlayer({"vote_nominate": "p1"}),
    }
    candidate = run_vote_nominate(state, actors)
    assert candidate == "p3"


def test_nominate_tie_returns_none():
    players = [
        Player(id="p1", name="A", role=Role.CIVILIAN),
        Player(id="p2", name="B", role=Role.CIVILIAN),
        Player(id="p3", name="C", role=Role.MAFIA, is_mafia_boss=True),
        Player(id="p4", name="D", role=Role.CIVILIAN),
    ]
    state = GameState(players=players, day_number=1, phase=Phase.VOTE_NOMINATE)
    actors = {
        "p1": MockPlayer({"vote_nominate": "p3"}),
        "p2": MockPlayer({"vote_nominate": "p4"}),
        "p3": MockPlayer({"vote_nominate": "p1"}),
        "p4": MockPlayer({"vote_nominate": "p2"}),
    }
    candidate = run_vote_nominate(state, actors)
    assert candidate is None


def test_nominate_cleric_vote_counts_double():
    players = [
        Player(id="p1", name="A", role=Role.CLERIC),
        Player(id="p2", name="B", role=Role.CIVILIAN),
        Player(id="p3", name="C", role=Role.MAFIA, is_mafia_boss=True),
    ]
    state = GameState(players=players, day_number=1, phase=Phase.VOTE_NOMINATE, cleric_id="p1")
    actors = {
        "p1": MockPlayer({"vote_nominate": "p3"}),  # +2
        "p2": MockPlayer({"vote_nominate": "p1"}),  # +1
        "p3": MockPlayer({"vote_nominate": "p2"}),  # +1
    }
    candidate = run_vote_nominate(state, actors)
    assert candidate == "p3"

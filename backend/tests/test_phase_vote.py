from mafia.models import GameState, Phase, Player, Role
from mafia.phases.vote import run_last_words, run_vote_nominate, run_vote_updown
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


def test_last_words_records_candidate_text():
    players = [
        Player(id="p1", name="A", role=Role.CIVILIAN),
        Player(id="p2", name="B", role=Role.MAFIA, is_mafia_boss=True),
    ]
    state = GameState(players=players, day_number=1, phase=Phase.LAST_WORDS)
    actors = {
        "p1": MockPlayer({}),
        "p2": MockPlayer({"last_words": "저는 시민이에요!"}),
    }
    run_last_words(state, actors, candidate_id="p2")
    entries = [e for e in state.public_log if e["kind"] == "last_words"]
    assert entries[-1]["speaker_id"] == "p2"
    assert entries[-1]["text"] == "저는 시민이에요!"


def test_updown_yes_majority_executes():
    players = [
        Player(id="p1", name="A", role=Role.CIVILIAN),
        Player(id="p2", name="B", role=Role.CIVILIAN),
        Player(id="p3", name="C", role=Role.MAFIA, is_mafia_boss=True),
    ]
    state = GameState(players=players, day_number=1, phase=Phase.VOTE_UPDOWN)
    actors = {
        "p1": MockPlayer({"vote_updown": "yes"}),
        "p2": MockPlayer({"vote_updown": "yes"}),
        "p3": MockPlayer({}),  # candidate doesn't vote
    }
    executed = run_vote_updown(state, actors, candidate_id="p3")
    assert executed is True
    assert state.player_by_id("p3").alive is False


def test_updown_no_majority_spares():
    players = [
        Player(id="p1", name="A", role=Role.CIVILIAN),
        Player(id="p2", name="B", role=Role.CIVILIAN),
        Player(id="p3", name="C", role=Role.MAFIA, is_mafia_boss=True),
    ]
    state = GameState(players=players, day_number=1, phase=Phase.VOTE_UPDOWN)
    actors = {
        "p1": MockPlayer({"vote_updown": "no"}),
        "p2": MockPlayer({"vote_updown": "no"}),
        "p3": MockPlayer({}),
    }
    executed = run_vote_updown(state, actors, candidate_id="p3")
    assert executed is False
    assert state.player_by_id("p3").alive is True


def test_updown_tie_spares():
    players = [
        Player(id="p1", name="A", role=Role.CIVILIAN),
        Player(id="p2", name="B", role=Role.CIVILIAN),
        Player(id="p3", name="C", role=Role.MAFIA, is_mafia_boss=True),
    ]
    state = GameState(players=players, day_number=1, phase=Phase.VOTE_UPDOWN)
    actors = {
        "p1": MockPlayer({"vote_updown": "yes"}),
        "p2": MockPlayer({"vote_updown": "no"}),
        "p3": MockPlayer({}),
    }
    executed = run_vote_updown(state, actors, candidate_id="p3")
    assert executed is False
    assert state.player_by_id("p3").alive is True


def test_updown_cleric_vote_counts_double():
    players = [
        Player(id="p1", name="A", role=Role.CLERIC),
        Player(id="p2", name="B", role=Role.CIVILIAN),
        Player(id="p3", name="C", role=Role.MAFIA, is_mafia_boss=True),
    ]
    state = GameState(players=players, day_number=1, phase=Phase.VOTE_UPDOWN, cleric_id="p1")
    actors = {
        "p1": MockPlayer({"vote_updown": "yes"}),  # +2
        "p2": MockPlayer({"vote_updown": "no"}),    # +1
        "p3": MockPlayer({}),
    }
    executed = run_vote_updown(state, actors, candidate_id="p3")
    assert executed is True

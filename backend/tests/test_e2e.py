import random

from mafia.engine import run_game, setup_game
from mafia.models import Phase, Role, Team
from mafia.player import MockPlayer


def test_e2e_civilians_win_when_they_always_vote_mafia():
    """Citizens nominate the mafia every day → mafia dies → citizens win."""
    state = setup_game(player_count=4, rng=random.Random(2026))
    mafia_id = next(p.id for p in state.players if p.role == Role.MAFIA)
    first_civ_id = next(p.id for p in state.players if p.role == Role.CIVILIAN)

    actors = {}
    for p in state.players:
        actors[p.id] = MockPlayer(
            {
                "speak_turn": "talk",
                "freetalk_eagerness": 5,
                "speak_freetalk": "talk",
                "vote_nominate": mafia_id,
                "vote_updown": "yes",
                "last_words": "안녕히",
                "night_kill": first_civ_id,
                "night_doctor_protect": first_civ_id,
                "night_police_investigate": mafia_id,
            }
        )

    winner = run_game(state, actors, max_days=20)
    assert winner == Team.CITIZEN.value
    assert state.phase == Phase.GAME_OVER
    assert not state.player_by_id(mafia_id).alive


def test_e2e_mafia_wins_when_citizens_misvote():
    """Citizens nominate each other and mafia kills win parity."""
    state = setup_game(player_count=4, rng=random.Random(11))
    mafia_id = next(p.id for p in state.players if p.role == Role.MAFIA)
    civs = [p.id for p in state.players if p.role == Role.CIVILIAN]

    target_civ = civs[0]
    actors = {}
    for p in state.players:
        actors[p.id] = MockPlayer(
            {
                "speak_turn": "talk",
                "freetalk_eagerness": 3,
                "speak_freetalk": "talk",
                "vote_nominate": target_civ,
                "vote_updown": "yes",
                "last_words": "...",
                "night_kill": civs[1] if len(civs) > 1 else civs[0],
                "night_doctor_protect": mafia_id,
                "night_police_investigate": civs[0],
            }
        )

    winner = run_game(state, actors, max_days=20)
    assert winner == Team.MAFIA.value
    assert state.phase == Phase.GAME_OVER


def test_e2e_8_player_game_terminates():
    """Larger game with cleric and multiple mafia still terminates."""
    state = setup_game(player_count=8, rng=random.Random(99))
    mafia = [p for p in state.players if p.role == Role.MAFIA]
    civs = [p for p in state.players if p.role == Role.CIVILIAN]
    boss = next(m for m in mafia if m.is_mafia_boss)
    kill_target = civs[0].id

    actors = {}
    for p in state.players:
        actors[p.id] = MockPlayer(
            {
                "speak_turn": "talk",
                "freetalk_eagerness": 5,
                "speak_freetalk": "talk",
                "vote_nominate": mafia[0].id,
                "vote_updown": "yes",
                "last_words": "끝",
                "night_kill": kill_target,
                "night_boss_propose": kill_target,
                "night_underling_respond": "yes",
                "night_boss_dialog": {"text": "확정", "final_target_id": kill_target},
                "night_doctor_protect": kill_target,
                "night_police_investigate": boss.id,
            }
        )

    winner = run_game(state, actors, max_days=30)
    # Static MockPlayer + doctor blocking the kill target can deadlock once the
    # nominated mafia is executed; "draw" still proves termination within max_days.
    assert winner in {Team.CITIZEN.value, Team.MAFIA.value, "draw"}
    assert state.phase == Phase.GAME_OVER

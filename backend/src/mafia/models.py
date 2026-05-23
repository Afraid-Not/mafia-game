"""Core enums and dataclasses for the mafia game."""
from __future__ import annotations

from enum import Enum


class Team(Enum):
    MAFIA = "mafia"
    CITIZEN = "citizen"


class Role(Enum):
    MAFIA = "mafia"
    CIVILIAN = "civilian"
    POLICE = "police"
    DOCTOR = "doctor"
    CLERIC = "cleric"  # 성직자: 투표 시 2표, 정체 비공개

    @property
    def team(self) -> Team:
        return Team.MAFIA if self is Role.MAFIA else Team.CITIZEN


class Phase(Enum):
    LOBBY = "lobby"
    NIGHT = "night"
    DAY_ROUNDROBIN = "day_roundrobin"
    DAY_FREETALK = "day_freetalk"
    VOTE_NOMINATE = "vote_nominate"
    LAST_WORDS = "last_words"
    VOTE_UPDOWN = "vote_updown"
    CHECK_WIN = "check_win"
    GAME_OVER = "game_over"

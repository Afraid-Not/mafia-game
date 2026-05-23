"""Core enums and dataclasses for the mafia game."""
from __future__ import annotations

from dataclasses import dataclass, field
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


@dataclass
class Player:
    id: str
    name: str
    role: Role
    is_mafia_boss: bool = False
    alive: bool = True
    # Private memory — info only this player should know
    known_mafia_ids: list[str] = field(default_factory=list)        # mafia knows allies
    police_investigations: list[tuple[str, bool]] = field(default_factory=list)
    doctor_protections: list[str] = field(default_factory=list)     # day_number index


@dataclass
class GameState:
    players: list[Player]
    day_number: int
    phase: Phase
    # Public log = all messages visible to everyone
    public_log: list[dict] = field(default_factory=list)
    # Private mafia chat log (only mafia see this)
    mafia_log: list[dict] = field(default_factory=list)
    # Last night's outcome (for day announcement)
    last_night_death: str | None = None
    # Special-role flag: cleric id (hidden from everyone except the cleric)
    cleric_id: str | None = None
    winner: Team | None = None

    def alive_players(self) -> list[Player]:
        return [p for p in self.players if p.alive]

    def player_by_id(self, pid: str) -> Player:
        for p in self.players:
            if p.id == pid:
                return p
        raise KeyError(pid)

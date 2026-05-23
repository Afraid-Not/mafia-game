# Agentic Mafia Game — Phase 1: Backend Game Engine Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** LLM 없이 작동하는 마피아 게임 백엔드 엔진. 결정론적 mock 플레이어로 4~11명 한 판을 끝까지 굴리며 전 상태머신·룰·페이즈가 단위 테스트로 검증된다.

**Architecture:** 단일 Python 패키지(`mafia/`). `GameEngine`이 페이즈 상태머신을 돌리고, 각 페이즈가 `Player` 프로토콜을 통해 결정을 요청한다. Phase 1에서는 `MockPlayer`만 제공하고, Phase 2에서 `LLMAgent`로 교체된다. LLM·웹 의존성 없음.

**Tech Stack:** Python 3.12, pytest, ruff (lint/format), dataclasses, Enum, typing.Protocol.

**Scope (Phase 1):**
- 포함: civilian, police, doctor, mafia(boss+underling), 성직자(특수). 4~11명 지원. 모든 페이즈 흐름. 결정론적 e2e 테스트.
- 제외: LLM 호출, 페르소나 풀, 발언 텍스트 생성, 웹/WebSocket, 기자·연인 역할.

**Reference spec:** `docs/superpowers/specs/2026-05-23-agentic-mafia-game-design.md`

---

## File Structure

```
backend/
├── pyproject.toml
├── README.md
├── src/mafia/
│   ├── __init__.py
│   ├── models.py             # Role, Phase enums; Player, GameState dataclasses
│   ├── rules.py              # role distribution, win conditions, vote weight
│   ├── player.py             # PlayerInterface protocol, MockPlayer, DecisionContext
│   ├── engine.py             # GameEngine (state machine driver)
│   └── phases/
│       ├── __init__.py
│       ├── night.py          # run_night()
│       ├── day.py            # run_day_roundrobin(), run_day_freetalk()
│       └── vote.py           # run_vote_nominate(), run_last_words(), run_vote_updown()
└── tests/
    ├── conftest.py           # shared fixtures
    ├── test_rules.py
    ├── test_player.py
    ├── test_phase_night.py
    ├── test_phase_day.py
    ├── test_phase_vote.py
    ├── test_engine.py
    └── test_e2e.py
```

---

## Task 1: Project Scaffolding

**Files:**
- Create: `backend/pyproject.toml`
- Create: `backend/README.md`
- Create: `backend/src/mafia/__init__.py`
- Create: `backend/tests/conftest.py`
- Create: `.gitignore`

- [ ] **Step 1: Create `backend/pyproject.toml`**

```toml
[project]
name = "mafia"
version = "0.1.0"
requires-python = ">=3.12"
dependencies = []

[project.optional-dependencies]
dev = ["pytest>=8.0", "ruff>=0.5"]

[build-system]
requires = ["setuptools>=68"]
build-backend = "setuptools.build_meta"

[tool.setuptools.packages.find]
where = ["src"]

[tool.pytest.ini_options]
testpaths = ["tests"]
addopts = "-v"

[tool.ruff]
line-length = 100
target-version = "py312"

[tool.ruff.lint]
select = ["E", "F", "W", "I", "B", "UP"]
```

- [ ] **Step 2: Create `backend/src/mafia/__init__.py`**

```python
"""Agentic Mafia Game — core engine."""
__version__ = "0.1.0"
```

- [ ] **Step 3: Create `backend/tests/conftest.py`**

```python
"""Shared pytest fixtures live here. Populated as tasks need them."""
```

- [ ] **Step 4: Create `backend/README.md`**

```markdown
# Agentic Mafia Game — Backend (Phase 1)

LLM 없이 동작하는 게임 엔진. mock 플레이어로 전 페이즈가 결정론적으로 돌아간다.

## Setup

```bash
cd backend
python3.12 -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
```

## Test

```bash
pytest
```

## Lint

```bash
ruff check src tests
ruff format src tests
```
```

- [ ] **Step 5: Create `.gitignore` at repo root**

```
# Python
__pycache__/
*.py[cod]
*.egg-info/
.venv/
.pytest_cache/
.ruff_cache/
.mypy_cache/

# Editors
.vscode/
.idea/

# OS
.DS_Store
```

- [ ] **Step 6: Install and verify**

Run:
```bash
cd backend && python3.12 -m venv .venv && source .venv/bin/activate && pip install -e ".[dev]"
pytest
```

Expected output (pytest): `no tests ran` 또는 빈 결과 — 에러 없이 종료.

- [ ] **Step 7: Commit**

```bash
git add backend/ .gitignore
git commit -m "chore: scaffold backend package for Phase 1"
```

---

## Task 2: Core Enums — Role and Phase

**Files:**
- Create: `backend/src/mafia/models.py`
- Test: `backend/tests/test_models.py`

- [ ] **Step 1: Write the failing test**

Create `backend/tests/test_models.py`:
```python
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
```

- [ ] **Step 2: Run test, verify failure**

Run: `cd backend && pytest tests/test_models.py -v`
Expected: ImportError / ModuleNotFoundError on `mafia.models`.

- [ ] **Step 3: Create `backend/src/mafia/models.py`**

```python
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
```

- [ ] **Step 4: Run test, verify pass**

Run: `cd backend && pytest tests/test_models.py -v`
Expected: 2 passed.

- [ ] **Step 5: Commit**

```bash
git add backend/src/mafia/models.py backend/tests/test_models.py
git commit -m "feat: add Role, Team, Phase enums"
```

---

## Task 3: Player and GameState Dataclasses

**Files:**
- Modify: `backend/src/mafia/models.py`
- Modify: `backend/tests/test_models.py`

- [ ] **Step 1: Add tests for Player and GameState**

Append to `backend/tests/test_models.py`:
```python
from mafia.models import Player, GameState


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
```

- [ ] **Step 2: Run, verify failure**

Run: `cd backend && pytest tests/test_models.py -v`
Expected: ImportError on Player/GameState.

- [ ] **Step 3: Extend `backend/src/mafia/models.py`**

Append:
```python
from dataclasses import dataclass, field


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
```

- [ ] **Step 4: Run, verify pass**

Run: `cd backend && pytest tests/test_models.py -v`
Expected: 6 passed.

- [ ] **Step 5: Commit**

```bash
git add backend/src/mafia/models.py backend/tests/test_models.py
git commit -m "feat: add Player and GameState dataclasses"
```

---

## Task 4: Rules — Role Distribution by Player Count

**Files:**
- Create: `backend/src/mafia/rules.py`
- Test: `backend/tests/test_rules.py`

- [ ] **Step 1: Write failing tests**

Create `backend/tests/test_rules.py`:
```python
from collections import Counter

import pytest

from mafia.models import Role
from mafia.rules import role_distribution


@pytest.mark.parametrize(
    "n,expected",
    [
        (4, {Role.MAFIA: 1, Role.POLICE: 1, Role.CIVILIAN: 2}),
        (5, {Role.MAFIA: 1, Role.POLICE: 1, Role.CIVILIAN: 3}),
        (6, {Role.MAFIA: 2, Role.POLICE: 1, Role.DOCTOR: 1, Role.CIVILIAN: 2}),
        (7, {Role.MAFIA: 2, Role.POLICE: 1, Role.DOCTOR: 1, Role.CIVILIAN: 3}),
        (8, {Role.MAFIA: 3, Role.POLICE: 1, Role.DOCTOR: 1, Role.CLERIC: 1, Role.CIVILIAN: 2}),
        (9, {Role.MAFIA: 3, Role.POLICE: 1, Role.DOCTOR: 1, Role.CLERIC: 1, Role.CIVILIAN: 3}),
        (10, {Role.MAFIA: 4, Role.POLICE: 1, Role.DOCTOR: 1, Role.CLERIC: 1, Role.CIVILIAN: 3}),
        (11, {Role.MAFIA: 4, Role.POLICE: 1, Role.DOCTOR: 1, Role.CLERIC: 1, Role.CIVILIAN: 4}),
    ],
)
def test_role_distribution(n, expected):
    roles = role_distribution(n)
    assert len(roles) == n
    assert Counter(roles) == Counter(expected)


@pytest.mark.parametrize("n", [0, 1, 2, 3, 12, 100])
def test_role_distribution_out_of_range(n):
    with pytest.raises(ValueError):
        role_distribution(n)
```

Note: Phase 1 simplifies the 10-11명 spec table by including only 1 cleric (no 연인/기자). Civilian count adjusted accordingly.

- [ ] **Step 2: Run, verify failure**

Run: `cd backend && pytest tests/test_rules.py -v`
Expected: ImportError on `mafia.rules`.

- [ ] **Step 3: Create `backend/src/mafia/rules.py`**

```python
"""Game rules: role distribution and win conditions."""
from __future__ import annotations

from mafia.models import GameState, Player, Role, Team

# (mafia, police, doctor, cleric) for player counts 4..11. Civilians fill the rest.
_DISTRIBUTION_TABLE: dict[int, tuple[int, int, int, int]] = {
    4: (1, 1, 0, 0),
    5: (1, 1, 0, 0),
    6: (2, 1, 1, 0),
    7: (2, 1, 1, 0),
    8: (3, 1, 1, 1),
    9: (3, 1, 1, 1),
    10: (4, 1, 1, 1),
    11: (4, 1, 1, 1),
}


def role_distribution(n: int) -> list[Role]:
    """Return a list of n roles for the given player count."""
    if n not in _DISTRIBUTION_TABLE:
        raise ValueError(f"player count {n} not supported (must be 4..11)")
    mafia, police, doctor, cleric = _DISTRIBUTION_TABLE[n]
    civilians = n - mafia - police - doctor - cleric
    roles: list[Role] = []
    roles.extend([Role.MAFIA] * mafia)
    roles.extend([Role.POLICE] * police)
    roles.extend([Role.DOCTOR] * doctor)
    roles.extend([Role.CLERIC] * cleric)
    roles.extend([Role.CIVILIAN] * civilians)
    return roles
```

- [ ] **Step 4: Run, verify pass**

Run: `cd backend && pytest tests/test_rules.py -v`
Expected: 14 passed (8 parametrized happy paths + 6 invalid).

- [ ] **Step 5: Commit**

```bash
git add backend/src/mafia/rules.py backend/tests/test_rules.py
git commit -m "feat: role distribution by player count"
```

---

## Task 5: Rules — Win Conditions and Vote Weight

**Files:**
- Modify: `backend/src/mafia/rules.py`
- Modify: `backend/tests/test_rules.py`

- [ ] **Step 1: Write failing tests**

Append to `backend/tests/test_rules.py`:
```python
from mafia.models import GameState, Phase, Player
from mafia.rules import check_winner, vote_weight


def _state(players: list[Player], cleric_id: str | None = None) -> GameState:
    return GameState(players=players, day_number=0, phase=Phase.LOBBY, cleric_id=cleric_id)


def test_check_winner_citizens_when_all_mafia_dead():
    players = [
        Player(id="p1", name="A", role=Role.MAFIA, alive=False),
        Player(id="p2", name="B", role=Role.CIVILIAN, alive=True),
        Player(id="p3", name="C", role=Role.CIVILIAN, alive=True),
    ]
    assert check_winner(_state(players)) == Team.CITIZEN


def test_check_winner_mafia_when_parity():
    players = [
        Player(id="p1", name="A", role=Role.MAFIA, alive=True),
        Player(id="p2", name="B", role=Role.CIVILIAN, alive=True),
    ]
    assert check_winner(_state(players)) == Team.MAFIA


def test_check_winner_mafia_when_majority():
    players = [
        Player(id="p1", name="A", role=Role.MAFIA, alive=True),
        Player(id="p2", name="B", role=Role.MAFIA, alive=True),
        Player(id="p3", name="C", role=Role.CIVILIAN, alive=True),
    ]
    assert check_winner(_state(players)) == Team.MAFIA


def test_check_winner_none_when_game_active():
    players = [
        Player(id="p1", name="A", role=Role.MAFIA, alive=True),
        Player(id="p2", name="B", role=Role.CIVILIAN, alive=True),
        Player(id="p3", name="C", role=Role.CIVILIAN, alive=True),
    ]
    assert check_winner(_state(players)) is None


def test_vote_weight_cleric_is_two():
    players = [Player(id="p1", name="A", role=Role.CLERIC)]
    state = _state(players, cleric_id="p1")
    assert vote_weight(state, "p1") == 2


def test_vote_weight_non_cleric_is_one():
    players = [Player(id="p1", name="A", role=Role.CIVILIAN)]
    state = _state(players, cleric_id=None)
    assert vote_weight(state, "p1") == 1
```

- [ ] **Step 2: Run, verify failure**

Run: `cd backend && pytest tests/test_rules.py -v`
Expected: ImportError on `check_winner`, `vote_weight`.

- [ ] **Step 3: Extend `backend/src/mafia/rules.py`**

Append:
```python
def check_winner(state: GameState) -> Team | None:
    """Return the winning team if game is over, else None."""
    alive = state.alive_players()
    alive_mafia = [p for p in alive if p.role.team == Team.MAFIA]
    alive_citizens = [p for p in alive if p.role.team == Team.CITIZEN]
    if not alive_mafia:
        return Team.CITIZEN
    if len(alive_mafia) >= len(alive_citizens):
        return Team.MAFIA
    return None


def vote_weight(state: GameState, voter_id: str) -> int:
    """Vote weight for a given voter (2 for cleric, 1 otherwise)."""
    if state.cleric_id == voter_id:
        return 2
    return 1
```

- [ ] **Step 4: Run, verify pass**

Run: `cd backend && pytest tests/test_rules.py -v`
Expected: all tests pass.

- [ ] **Step 5: Commit**

```bash
git add backend/src/mafia/rules.py backend/tests/test_rules.py
git commit -m "feat: win condition and cleric vote weight"
```

---

## Task 6: Player Interface and MockPlayer

**Files:**
- Create: `backend/src/mafia/player.py`
- Test: `backend/tests/test_player.py`

- [ ] **Step 1: Write failing tests**

Create `backend/tests/test_player.py`:
```python
from mafia.models import GameState, Phase, Player, Role
from mafia.player import DecisionContext, MockPlayer


def _ctx(state: GameState, actor_id: str, action: str, **payload) -> DecisionContext:
    return DecisionContext(state=state, actor_id=actor_id, action=action, payload=payload)


def test_mock_speak_turn_returns_canned_text():
    p = MockPlayer(scripted={"speak_turn": "I am a citizen"})
    ctx = _ctx(GameState(players=[], day_number=1, phase=Phase.DAY_ROUNDROBIN), "p1", "speak_turn")
    out = p.decide(ctx)
    assert out == {"text": "I am a citizen"}


def test_mock_vote_nominate_returns_target():
    p = MockPlayer(scripted={"vote_nominate": "p2"})
    ctx = _ctx(GameState(players=[], day_number=1, phase=Phase.VOTE_NOMINATE), "p1", "vote_nominate")
    out = p.decide(ctx)
    assert out == {"target_id": "p2", "reasoning": "mock"}


def test_mock_freetalk_eagerness_and_text():
    p = MockPlayer(scripted={"speak_freetalk": {"eagerness": 7, "text": "hmm"}})
    ctx = _ctx(GameState(players=[], day_number=1, phase=Phase.DAY_FREETALK), "p1", "speak_freetalk")
    out = p.decide(ctx)
    assert out == {"eagerness": 7, "text": "hmm"}


def test_mock_missing_action_raises():
    p = MockPlayer(scripted={})
    ctx = _ctx(GameState(players=[], day_number=1, phase=Phase.NIGHT), "p1", "night_kill")
    import pytest
    with pytest.raises(KeyError):
        p.decide(ctx)
```

- [ ] **Step 2: Run, verify failure**

Run: `cd backend && pytest tests/test_player.py -v`
Expected: ImportError.

- [ ] **Step 3: Create `backend/src/mafia/player.py`**

```python
"""Player interface: protocol all decision-makers (mock or LLM) implement."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Protocol

from mafia.models import GameState


@dataclass
class DecisionContext:
    """Everything a player needs to make a decision for one action."""
    state: GameState
    actor_id: str
    action: str  # e.g. "speak_turn", "vote_nominate", "night_kill", ...
    payload: dict[str, Any] = field(default_factory=dict)


class PlayerInterface(Protocol):
    """Anything that can make decisions for a Player implements this."""
    def decide(self, ctx: DecisionContext) -> dict[str, Any]: ...


class MockPlayer:
    """Returns scripted responses keyed by action name.

    For `speak_turn`, `last_words`: scripted value is a str → wrapped as {"text": ...}.
    For `vote_nominate`, `vote_updown`, `night_kill`, `night_doctor_protect`,
      `night_police_investigate`, `night_boss_propose`, `night_underling_respond`,
      `night_boss_dialog`, `mafia_chat`: scripted value is the target id or a dict.
    For `speak_freetalk`: scripted value is a dict with `eagerness` and `text`.
    """

    def __init__(self, scripted: dict[str, Any]):
        self._scripted = scripted

    def decide(self, ctx: DecisionContext) -> dict[str, Any]:
        if ctx.action not in self._scripted:
            raise KeyError(f"MockPlayer has no scripted response for action={ctx.action}")
        raw = self._scripted[ctx.action]

        if ctx.action in ("speak_turn", "last_words", "mafia_chat"):
            return {"text": raw if isinstance(raw, str) else raw["text"]}

        if ctx.action == "speak_freetalk":
            return {"eagerness": raw["eagerness"], "text": raw["text"]}

        if ctx.action in (
            "vote_nominate",
            "night_kill",
            "night_doctor_protect",
            "night_police_investigate",
        ):
            if isinstance(raw, str):
                return {"target_id": raw, "reasoning": "mock"}
            return raw

        if ctx.action == "vote_updown":
            if isinstance(raw, str):
                return {"vote": raw, "reasoning": "mock"}
            return raw

        if ctx.action == "night_boss_propose":
            if isinstance(raw, str):
                return {"target_id": raw, "reasoning": "mock", "text": f"오늘은 {raw}"}
            return raw

        if ctx.action == "night_underling_respond":
            if isinstance(raw, str):
                return {"agree": raw, "reasoning": "mock", "text": ""}
            return raw

        if ctx.action == "night_boss_dialog":
            return raw if isinstance(raw, dict) else {"text": raw, "final_target_id": None}

        # Fallback: return raw as-is if it's a dict
        if isinstance(raw, dict):
            return raw
        raise ValueError(f"unhandled mock action {ctx.action} with raw={raw!r}")
```

- [ ] **Step 4: Run, verify pass**

Run: `cd backend && pytest tests/test_player.py -v`
Expected: 4 passed.

- [ ] **Step 5: Commit**

```bash
git add backend/src/mafia/player.py backend/tests/test_player.py
git commit -m "feat: PlayerInterface protocol and MockPlayer"
```

---

## Task 7: Phases Package Skeleton

**Files:**
- Create: `backend/src/mafia/phases/__init__.py`

- [ ] **Step 1: Create empty `backend/src/mafia/phases/__init__.py`**

```python
"""Phase handlers: night, day, vote."""
```

- [ ] **Step 2: Commit**

```bash
git add backend/src/mafia/phases/__init__.py
git commit -m "chore: phases package skeleton"
```

---

## Task 8: Night Phase — Single Mafia Kill

**Files:**
- Create: `backend/src/mafia/phases/night.py`
- Test: `backend/tests/test_phase_night.py`

- [ ] **Step 1: Write failing test**

Create `backend/tests/test_phase_night.py`:
```python
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
```

- [ ] **Step 2: Run, verify failure**

Run: `cd backend && pytest tests/test_phase_night.py -v`
Expected: ImportError.

- [ ] **Step 3: Create `backend/src/mafia/phases/night.py`**

```python
"""Night phase: mafia kill, doctor protect, police investigate."""
from __future__ import annotations

from mafia.models import GameState, Player, Role, Team
from mafia.player import DecisionContext, PlayerInterface


def _alive_mafia(state: GameState) -> list[Player]:
    return [p for p in state.alive_players() if p.role == Role.MAFIA]


def _alive_non_mafia(state: GameState) -> list[Player]:
    return [p for p in state.alive_players() if p.role.team != Team.MAFIA]


def _decide_mafia_target_single(
    state: GameState, mafia: Player, actors: dict[str, PlayerInterface]
) -> str:
    ctx = DecisionContext(state=state, actor_id=mafia.id, action="night_kill")
    return actors[mafia.id].decide(ctx)["target_id"]


def run_night(state: GameState, actors: dict[str, PlayerInterface]) -> None:
    """Execute night actions and mutate `state` in place.

    Phase 1 scope: single-mafia kill with no doctor/police yet (extended in next tasks).
    """
    mafia = _alive_mafia(state)
    if not mafia:
        state.last_night_death = None
        return

    if len(mafia) == 1:
        target_id = _decide_mafia_target_single(state, mafia[0], actors)
    else:
        # extended in Task 9
        raise NotImplementedError("multi-mafia not implemented yet")

    # No doctor/police yet — extended in Tasks 10/11.
    target = state.player_by_id(target_id)
    target.alive = False
    state.last_night_death = target.id
```

- [ ] **Step 4: Run, verify pass**

Run: `cd backend && pytest tests/test_phase_night.py -v`
Expected: 1 passed.

- [ ] **Step 5: Commit**

```bash
git add backend/src/mafia/phases/night.py backend/tests/test_phase_night.py
git commit -m "feat: night phase — single mafia kill"
```

---

## Task 9: Night Phase — Multi-Mafia Boss/Underling

**Files:**
- Modify: `backend/src/mafia/phases/night.py`
- Modify: `backend/tests/test_phase_night.py`

- [ ] **Step 1: Add failing tests**

Append to `backend/tests/test_phase_night.py`:
```python
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
```

- [ ] **Step 2: Run, verify failure**

Run: `cd backend && pytest tests/test_phase_night.py -v`
Expected: NotImplementedError for the new tests.

- [ ] **Step 3: Replace the `else` branch in `run_night`**

In `backend/src/mafia/phases/night.py`, replace the multi-mafia branch and add helpers:

```python
def _decide_mafia_target_multi(
    state: GameState, mafia: list[Player], actors: dict[str, PlayerInterface]
) -> str:
    boss = next(m for m in mafia if m.is_mafia_boss)
    underlings = [m for m in mafia if not m.is_mafia_boss]

    propose = actors[boss.id].decide(
        DecisionContext(state=state, actor_id=boss.id, action="night_boss_propose")
    )
    proposed_target = propose["target_id"]
    state.mafia_log.append({"speaker_id": boss.id, "text": propose.get("text", ""),
                            "kind": "propose", "target_id": proposed_target})

    disagreements: list[Player] = []
    for u in underlings:
        resp = actors[u.id].decide(
            DecisionContext(
                state=state,
                actor_id=u.id,
                action="night_underling_respond",
                payload={"proposed_target_id": proposed_target},
            )
        )
        state.mafia_log.append({"speaker_id": u.id, "text": resp.get("text", ""),
                                "kind": "respond", "agree": resp["agree"]})
        if resp["agree"] == "no":
            disagreements.append(u)

    if not disagreements:
        return proposed_target

    # Dialog rounds — at most 1 reply turn per dissenter, then boss finalizes.
    for d in disagreements:
        # one short exchange could be expanded; for Phase 1 we just record the disagreement.
        state.mafia_log.append({"speaker_id": d.id, "text": "(반대 표명)", "kind": "dissent"})

    final = actors[boss.id].decide(
        DecisionContext(
            state=state,
            actor_id=boss.id,
            action="night_boss_dialog",
            payload={"proposed_target_id": proposed_target,
                     "dissenters": [d.id for d in disagreements]},
        )
    )
    state.mafia_log.append({"speaker_id": boss.id, "text": final.get("text", ""),
                            "kind": "final"})
    final_target = final.get("final_target_id") or proposed_target
    return final_target
```

And update the `run_night` else branch:
```python
    if len(mafia) == 1:
        target_id = _decide_mafia_target_single(state, mafia[0], actors)
    else:
        target_id = _decide_mafia_target_multi(state, mafia, actors)
```

- [ ] **Step 4: Run, verify pass**

Run: `cd backend && pytest tests/test_phase_night.py -v`
Expected: 4 passed.

- [ ] **Step 5: Commit**

```bash
git add backend/src/mafia/phases/night.py backend/tests/test_phase_night.py
git commit -m "feat: multi-mafia boss/underling night decision"
```

---

## Task 10: Night Phase — Doctor Protection

**Files:**
- Modify: `backend/src/mafia/phases/night.py`
- Modify: `backend/tests/test_phase_night.py`

- [ ] **Step 1: Add failing tests**

Append to `backend/tests/test_phase_night.py`:
```python
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
```

- [ ] **Step 2: Run, verify failure**

Run: `cd backend && pytest tests/test_phase_night.py -v`

- [ ] **Step 3: Update `run_night` to handle doctor**

In `backend/src/mafia/phases/night.py`, modify `run_night`:
```python
def run_night(state: GameState, actors: dict[str, PlayerInterface]) -> None:
    mafia = _alive_mafia(state)
    if not mafia:
        state.last_night_death = None
        return

    if len(mafia) == 1:
        target_id = _decide_mafia_target_single(state, mafia[0], actors)
    else:
        target_id = _decide_mafia_target_multi(state, mafia, actors)

    # Doctor protection
    protected_id: str | None = None
    doctor = next((p for p in state.alive_players() if p.role == Role.DOCTOR), None)
    if doctor is not None:
        decision = actors[doctor.id].decide(
            DecisionContext(state=state, actor_id=doctor.id, action="night_doctor_protect")
        )
        protected_id = decision["target_id"]
        doctor.doctor_protections.append(protected_id)

    if protected_id == target_id:
        state.last_night_death = None
    else:
        target = state.player_by_id(target_id)
        target.alive = False
        state.last_night_death = target.id
```

- [ ] **Step 4: Run, verify pass**

Run: `cd backend && pytest tests/test_phase_night.py -v`
Expected: 6 passed.

- [ ] **Step 5: Commit**

```bash
git add backend/src/mafia/phases/night.py backend/tests/test_phase_night.py
git commit -m "feat: night phase — doctor protection"
```

---

## Task 11: Night Phase — Police Investigation

**Files:**
- Modify: `backend/src/mafia/phases/night.py`
- Modify: `backend/tests/test_phase_night.py`

- [ ] **Step 1: Add failing tests**

Append to `backend/tests/test_phase_night.py`:
```python
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
```

- [ ] **Step 2: Run, verify failure**

Run: `cd backend && pytest tests/test_phase_night.py -v`

- [ ] **Step 3: Update `run_night` to add police step**

In `backend/src/mafia/phases/night.py`, insert police step before the death resolution:
```python
    # Police investigation
    police = next((p for p in state.alive_players() if p.role == Role.POLICE), None)
    if police is not None:
        decision = actors[police.id].decide(
            DecisionContext(state=state, actor_id=police.id, action="night_police_investigate")
        )
        investigated = state.player_by_id(decision["target_id"])
        is_mafia = investigated.role == Role.MAFIA
        police.police_investigations.append((investigated.id, is_mafia))
```

Place it after the doctor block, before the death resolution.

- [ ] **Step 4: Run, verify pass**

Run: `cd backend && pytest tests/test_phase_night.py -v`
Expected: 8 passed.

- [ ] **Step 5: Commit**

```bash
git add backend/src/mafia/phases/night.py backend/tests/test_phase_night.py
git commit -m "feat: night phase — police investigation"
```

---

## Task 12: Day Phase — Round-Robin

**Files:**
- Create: `backend/src/mafia/phases/day.py`
- Test: `backend/tests/test_phase_day.py`

- [ ] **Step 1: Write failing test**

Create `backend/tests/test_phase_day.py`:
```python
from mafia.models import GameState, Phase, Player, Role
from mafia.phases.day import run_day_roundrobin
from mafia.player import MockPlayer


def test_roundrobin_collects_one_speech_per_alive_player():
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
    assert sorted(speakers) == ["p1", "p2"]
    assert "p3" not in speakers
```

- [ ] **Step 2: Run, verify failure**

Run: `cd backend && pytest tests/test_phase_day.py -v`
Expected: ImportError.

- [ ] **Step 3: Create `backend/src/mafia/phases/day.py`**

```python
"""Day phase: round-robin speeches and free-talk."""
from __future__ import annotations

from mafia.models import GameState
from mafia.player import DecisionContext, PlayerInterface


def run_day_roundrobin(state: GameState, actors: dict[str, PlayerInterface]) -> None:
    """Every alive player speaks once. Order = stable list order (Phase 1).

    Eagerness-based ordering will be applied in Task 13 (free talk) and refined later.
    """
    for player in state.alive_players():
        result = actors[player.id].decide(
            DecisionContext(state=state, actor_id=player.id, action="speak_turn")
        )
        state.public_log.append({
            "kind": "speak",
            "speaker_id": player.id,
            "text": result["text"],
            "day_number": state.day_number,
            "phase": "day_roundrobin",
        })
```

- [ ] **Step 4: Run, verify pass**

Run: `cd backend && pytest tests/test_phase_day.py -v`
Expected: 1 passed.

- [ ] **Step 5: Commit**

```bash
git add backend/src/mafia/phases/day.py backend/tests/test_phase_day.py
git commit -m "feat: day round-robin speeches"
```

---

## Task 13: Day Phase — Free Talk with Eagerness

**Files:**
- Modify: `backend/src/mafia/phases/day.py`
- Modify: `backend/tests/test_phase_day.py`

- [ ] **Step 1: Add failing test**

Append to `backend/tests/test_phase_day.py`:
```python
def test_freetalk_picks_highest_eagerness_per_round_max_2_rounds():
    players = [
        Player(id="p1", name="A", role=Role.CIVILIAN),
        Player(id="p2", name="B", role=Role.CIVILIAN),
        Player(id="p3", name="C", role=Role.CIVILIAN),
    ]
    state = GameState(players=players, day_number=1, phase=Phase.DAY_FREETALK)
    actors = {
        "p1": MockPlayer({"speak_freetalk": {"eagerness": 9, "text": "say9"}}),
        "p2": MockPlayer({"speak_freetalk": {"eagerness": 5, "text": "say5"}}),
        "p3": MockPlayer({"speak_freetalk": {"eagerness": 1, "text": "say1"}}),
    }
    run_day_freetalk(state, actors, max_rounds=2)
    speeches = [e for e in state.public_log if e["kind"] == "speak_freetalk"]
    # 2 rounds * 1 speaker per round = 2 entries, both from p1
    # (since p1 always has eagerness 9 and other actors are static here)
    assert len(speeches) == 2
    assert all(s["speaker_id"] == "p1" for s in speeches)
```

- [ ] **Step 2: Add import**

Update the existing import line in `backend/tests/test_phase_day.py`:
```python
from mafia.phases.day import run_day_freetalk, run_day_roundrobin
```

- [ ] **Step 3: Run, verify failure**

Run: `cd backend && pytest tests/test_phase_day.py -v`

- [ ] **Step 4: Append to `backend/src/mafia/phases/day.py`**

```python
def run_day_freetalk(
    state: GameState,
    actors: dict[str, PlayerInterface],
    max_rounds: int = 2,
) -> None:
    """Each round, every alive player returns an eagerness score; the highest speaks."""
    for _ in range(max_rounds):
        scores: list[tuple[int, str, str]] = []  # (eagerness, speaker_id, text)
        for player in state.alive_players():
            result = actors[player.id].decide(
                DecisionContext(state=state, actor_id=player.id, action="speak_freetalk")
            )
            scores.append((int(result["eagerness"]), player.id, result["text"]))
        scores.sort(reverse=True)
        eagerness, speaker_id, text = scores[0]
        state.public_log.append({
            "kind": "speak_freetalk",
            "speaker_id": speaker_id,
            "text": text,
            "eagerness": eagerness,
            "day_number": state.day_number,
        })
```

Cost note: in Phase 2 this will be replaced with a heuristic that does NOT call the LLM for non-speakers. For Phase 1 the mock cost is zero.

- [ ] **Step 5: Run, verify pass**

Run: `cd backend && pytest tests/test_phase_day.py -v`
Expected: 2 passed.

- [ ] **Step 6: Commit**

```bash
git add backend/src/mafia/phases/day.py backend/tests/test_phase_day.py
git commit -m "feat: day free-talk with eagerness-based picking"
```

---

## Task 14: Vote Phase — Nominate and Tally

**Files:**
- Create: `backend/src/mafia/phases/vote.py`
- Test: `backend/tests/test_phase_vote.py`

- [ ] **Step 1: Write failing test**

Create `backend/tests/test_phase_vote.py`:
```python
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
```

- [ ] **Step 2: Run, verify failure**

Run: `cd backend && pytest tests/test_phase_vote.py -v`
Expected: ImportError.

- [ ] **Step 3: Create `backend/src/mafia/phases/vote.py`**

```python
"""Vote phase: nominate, last words, up/down."""
from __future__ import annotations

from collections import Counter

from mafia.models import GameState
from mafia.player import DecisionContext, PlayerInterface
from mafia.rules import vote_weight


def run_vote_nominate(
    state: GameState, actors: dict[str, PlayerInterface]
) -> str | None:
    """Collect nominate votes; return the candidate id or None on tie / empty."""
    tally: Counter[str] = Counter()
    for voter in state.alive_players():
        decision = actors[voter.id].decide(
            DecisionContext(state=state, actor_id=voter.id, action="vote_nominate")
        )
        target_id = decision["target_id"]
        weight = vote_weight(state, voter.id)
        tally[target_id] += weight
        state.public_log.append({
            "kind": "vote_nominate",
            "voter_id": voter.id,
            "target_id": target_id,
            "weight": weight,
        })

    if not tally:
        return None
    top_count = max(tally.values())
    top_targets = [t for t, c in tally.items() if c == top_count]
    if len(top_targets) > 1:
        return None
    return top_targets[0]
```

- [ ] **Step 4: Run, verify pass**

Run: `cd backend && pytest tests/test_phase_vote.py -v`
Expected: 3 passed.

- [ ] **Step 5: Commit**

```bash
git add backend/src/mafia/phases/vote.py backend/tests/test_phase_vote.py
git commit -m "feat: vote nominate with tie-break and cleric weight"
```

---

## Task 15: Vote Phase — Last Words and Up/Down

**Files:**
- Modify: `backend/src/mafia/phases/vote.py`
- Modify: `backend/tests/test_phase_vote.py`

- [ ] **Step 1: Add failing tests**

Append to `backend/tests/test_phase_vote.py`:
```python
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
```

- [ ] **Step 2: Update imports in test file**

Update import in `backend/tests/test_phase_vote.py`:
```python
from mafia.phases.vote import run_last_words, run_vote_nominate, run_vote_updown
```

- [ ] **Step 3: Run, verify failure**

Run: `cd backend && pytest tests/test_phase_vote.py -v`

- [ ] **Step 4: Append to `backend/src/mafia/phases/vote.py`**

```python
def run_last_words(
    state: GameState,
    actors: dict[str, PlayerInterface],
    candidate_id: str,
) -> None:
    decision = actors[candidate_id].decide(
        DecisionContext(state=state, actor_id=candidate_id, action="last_words")
    )
    state.public_log.append({
        "kind": "last_words",
        "speaker_id": candidate_id,
        "text": decision["text"],
        "day_number": state.day_number,
    })


def run_vote_updown(
    state: GameState,
    actors: dict[str, PlayerInterface],
    candidate_id: str,
) -> bool:
    """Each alive non-candidate votes yes/no. Yes-majority → execute.

    Returns True if the candidate was executed.
    """
    yes_count = 0
    no_count = 0
    for voter in state.alive_players():
        if voter.id == candidate_id:
            continue
        decision = actors[voter.id].decide(
            DecisionContext(state=state, actor_id=voter.id, action="vote_updown")
        )
        weight = vote_weight(state, voter.id)
        if decision["vote"] == "yes":
            yes_count += weight
        else:
            no_count += weight
        state.public_log.append({
            "kind": "vote_updown",
            "voter_id": voter.id,
            "vote": decision["vote"],
            "weight": weight,
            "candidate_id": candidate_id,
        })

    executed = yes_count > no_count
    if executed:
        state.player_by_id(candidate_id).alive = False
        state.public_log.append({
            "kind": "execution",
            "candidate_id": candidate_id,
            "yes": yes_count,
            "no": no_count,
        })
    return executed
```

- [ ] **Step 5: Run, verify pass**

Run: `cd backend && pytest tests/test_phase_vote.py -v`
Expected: 8 passed.

- [ ] **Step 6: Commit**

```bash
git add backend/src/mafia/phases/vote.py backend/tests/test_phase_vote.py
git commit -m "feat: last words and up/down vote with cleric weight"
```

---

## Task 16: Engine — Game Setup

**Files:**
- Create: `backend/src/mafia/engine.py`
- Test: `backend/tests/test_engine.py`

- [ ] **Step 1: Write failing test**

Create `backend/tests/test_engine.py`:
```python
import random

from mafia.engine import setup_game
from mafia.models import Phase, Role, Team


def test_setup_game_assigns_correct_roles_for_6_players():
    state = setup_game(player_count=6, rng=random.Random(42))
    role_counts = {r: 0 for r in Role}
    for p in state.players:
        role_counts[p.role] += 1
    assert role_counts[Role.MAFIA] == 2
    assert role_counts[Role.POLICE] == 1
    assert role_counts[Role.DOCTOR] == 1
    assert role_counts[Role.CIVILIAN] == 2
    assert role_counts[Role.CLERIC] == 0


def test_setup_game_designates_one_mafia_boss():
    state = setup_game(player_count=8, rng=random.Random(1))
    mafia = [p for p in state.players if p.role == Role.MAFIA]
    bosses = [m for m in mafia if m.is_mafia_boss]
    assert len(bosses) == 1


def test_setup_game_known_mafia_ids_populated_for_each_mafia():
    state = setup_game(player_count=6, rng=random.Random(1))
    mafia_ids = sorted(p.id for p in state.players if p.role == Role.MAFIA)
    for m in state.players:
        if m.role == Role.MAFIA:
            assert sorted(m.known_mafia_ids) == [mid for mid in mafia_ids if mid != m.id]


def test_setup_game_sets_cleric_id_when_present():
    state = setup_game(player_count=8, rng=random.Random(1))
    cleric = next(p for p in state.players if p.role == Role.CLERIC)
    assert state.cleric_id == cleric.id


def test_setup_game_initial_phase_is_night():
    state = setup_game(player_count=4, rng=random.Random(1))
    assert state.phase == Phase.NIGHT
    assert state.day_number == 1


def test_setup_game_invalid_count_raises():
    import pytest
    with pytest.raises(ValueError):
        setup_game(player_count=3, rng=random.Random(0))
```

- [ ] **Step 2: Run, verify failure**

Run: `cd backend && pytest tests/test_engine.py -v`
Expected: ImportError.

- [ ] **Step 3: Create `backend/src/mafia/engine.py`**

```python
"""GameEngine: setup and state machine driver."""
from __future__ import annotations

import random
from collections.abc import Callable

from mafia.models import GameState, Phase, Player, Role
from mafia.phases.day import run_day_freetalk, run_day_roundrobin
from mafia.phases.night import run_night
from mafia.phases.vote import run_last_words, run_vote_nominate, run_vote_updown
from mafia.player import PlayerInterface
from mafia.rules import check_winner, role_distribution


def setup_game(player_count: int, rng: random.Random) -> GameState:
    """Initialize a game: assign roles, designate mafia boss, set cleric_id."""
    roles = role_distribution(player_count)
    rng.shuffle(roles)

    players: list[Player] = []
    for i, role in enumerate(roles, start=1):
        players.append(Player(id=f"p{i}", name=f"Player{i}", role=role))

    mafia = [p for p in players if p.role == Role.MAFIA]
    if mafia:
        boss = rng.choice(mafia)
        boss.is_mafia_boss = True
        mafia_ids = [m.id for m in mafia]
        for m in mafia:
            m.known_mafia_ids = [mid for mid in mafia_ids if mid != m.id]

    cleric = next((p for p in players if p.role == Role.CLERIC), None)

    return GameState(
        players=players,
        day_number=1,
        phase=Phase.NIGHT,
        cleric_id=cleric.id if cleric else None,
    )
```

- [ ] **Step 4: Run, verify pass**

Run: `cd backend && pytest tests/test_engine.py -v`
Expected: 6 passed.

- [ ] **Step 5: Commit**

```bash
git add backend/src/mafia/engine.py backend/tests/test_engine.py
git commit -m "feat: engine setup_game with role/boss/cleric assignment"
```

---

## Task 17: Engine — State Machine Driver

**Files:**
- Modify: `backend/src/mafia/engine.py`
- Modify: `backend/tests/test_engine.py`

- [ ] **Step 1: Add failing test**

Append to `backend/tests/test_engine.py`:
```python
import random

from mafia.engine import run_game
from mafia.player import MockPlayer


def _all_yes_actors(state, *, kill_target, nominate_target):
    """Helper to build a deterministic actor set."""
    actors: dict[str, MockPlayer] = {}
    for p in state.players:
        actors[p.id] = MockPlayer({
            "speak_turn": f"I am {p.id}",
            "speak_freetalk": {"eagerness": 5, "text": "talk"},
            "vote_nominate": nominate_target,
            "vote_updown": "yes",
            "last_words": "최후",
            "night_kill": kill_target,
            "night_boss_propose": kill_target,
            "night_underling_respond": "yes",
            "night_boss_dialog": {"text": "확정", "final_target_id": kill_target},
            "night_doctor_protect": p.id,
            "night_police_investigate": kill_target,
            "mafia_chat": "",
        })
    return actors


def test_run_game_terminates_with_winner_within_max_days():
    state = setup_game(player_count=4, rng=random.Random(7))
    # find one civilian to kill each night, one mafia to nominate each day
    civ = next(p for p in state.players if p.role == Role.CIVILIAN)
    maf = next(p for p in state.players if p.role == Role.MAFIA)
    actors = _all_yes_actors(state, kill_target=civ.id, nominate_target=maf.id)
    result = run_game(state, actors, max_days=20)
    assert result is not None
    assert state.phase == Phase.GAME_OVER
    assert state.winner is not None
```

- [ ] **Step 2: Run, verify failure**

Run: `cd backend && pytest tests/test_engine.py -v`

- [ ] **Step 3: Append to `backend/src/mafia/engine.py`**

```python
def run_game(
    state: GameState,
    actors: dict[str, PlayerInterface],
    max_days: int = 50,
) -> str:
    """Drive the state machine end-to-end. Returns the winning team name."""
    while state.day_number <= max_days:
        # NIGHT
        state.phase = Phase.NIGHT
        run_night(state, actors)
        winner = check_winner(state)
        if winner is not None:
            state.winner = winner
            state.phase = Phase.GAME_OVER
            return winner.value

        # DAY
        state.phase = Phase.DAY_ROUNDROBIN
        run_day_roundrobin(state, actors)

        state.phase = Phase.DAY_FREETALK
        run_day_freetalk(state, actors)

        # VOTE
        state.phase = Phase.VOTE_NOMINATE
        candidate_id = run_vote_nominate(state, actors)
        if candidate_id is not None:
            state.phase = Phase.LAST_WORDS
            run_last_words(state, actors, candidate_id)
            state.phase = Phase.VOTE_UPDOWN
            run_vote_updown(state, actors, candidate_id)

        winner = check_winner(state)
        if winner is not None:
            state.winner = winner
            state.phase = Phase.GAME_OVER
            return winner.value

        state.day_number += 1

    # Safety net: shouldn't reach here with sane inputs
    state.phase = Phase.GAME_OVER
    return "draw"
```

- [ ] **Step 4: Run, verify pass**

Run: `cd backend && pytest tests/test_engine.py -v`
Expected: all engine tests pass.

- [ ] **Step 5: Commit**

```bash
git add backend/src/mafia/engine.py backend/tests/test_engine.py
git commit -m "feat: run_game state machine driver"
```

---

## Task 18: End-to-End — Deterministic Full Game

**Files:**
- Test: `backend/tests/test_e2e.py`

- [ ] **Step 1: Write the test**

Create `backend/tests/test_e2e.py`:
```python
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
        actors[p.id] = MockPlayer({
            "speak_turn": "talk",
            "speak_freetalk": {"eagerness": 5, "text": "talk"},
            "vote_nominate": mafia_id,
            "vote_updown": "yes",
            "last_words": "안녕히",
            "night_kill": first_civ_id,
            "night_doctor_protect": first_civ_id,    # save target every night
            "night_police_investigate": mafia_id,
        })

    winner = run_game(state, actors, max_days=20)
    assert winner == Team.CITIZEN.value
    assert state.phase == Phase.GAME_OVER
    assert not state.player_by_id(mafia_id).alive


def test_e2e_mafia_wins_when_citizens_misvote():
    """Citizens nominate each other and mafia kills win parity."""
    state = setup_game(player_count=4, rng=random.Random(11))
    mafia_id = next(p.id for p in state.players if p.role == Role.MAFIA)
    civs = [p.id for p in state.players if p.role == Role.CIVILIAN]

    actors = {}
    # All vote for a civilian every day
    target_civ = civs[0]
    for p in state.players:
        # mafia kills a different civ each night cycle (only one civ to begin with)
        actors[p.id] = MockPlayer({
            "speak_turn": "talk",
            "speak_freetalk": {"eagerness": 3, "text": "talk"},
            "vote_nominate": target_civ,
            "vote_updown": "yes",
            "last_words": "...",
            "night_kill": civs[1] if len(civs) > 1 else civs[0],
            "night_doctor_protect": mafia_id,  # protect mafia (mistake)
            "night_police_investigate": civs[0],
        })

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
        actors[p.id] = MockPlayer({
            "speak_turn": "talk",
            "speak_freetalk": {"eagerness": 5, "text": "talk"},
            "vote_nominate": mafia[0].id,
            "vote_updown": "yes",
            "last_words": "끝",
            "night_kill": kill_target,
            "night_boss_propose": kill_target,
            "night_underling_respond": "yes",
            "night_boss_dialog": {"text": "확정", "final_target_id": kill_target},
            "night_doctor_protect": kill_target,
            "night_police_investigate": boss.id,
        })

    winner = run_game(state, actors, max_days=30)
    assert winner in {Team.CITIZEN.value, Team.MAFIA.value}
    assert state.phase == Phase.GAME_OVER
```

- [ ] **Step 2: Run all tests**

Run: `cd backend && pytest -v`
Expected: every test in the suite passes (rules, models, player, phases, engine, e2e).

- [ ] **Step 3: Lint and format**

Run:
```bash
cd backend
ruff format src tests
ruff check src tests
```
Expected: clean (no errors, no diff).

- [ ] **Step 4: Commit**

```bash
git add backend/tests/test_e2e.py
git commit -m "test: end-to-end deterministic game scenarios"
```

---

## Task 19: Final — Update Backend README

**Files:**
- Modify: `backend/README.md`

- [ ] **Step 1: Update README with status**

Replace `backend/README.md` content:
```markdown
# Agentic Mafia Game — Backend (Phase 1 complete)

Phase 1 deliverable: LLM 없이 결정론적 mock 플레이어로 마피아 게임 한 판이 끝까지 돌아가는 백엔드 엔진.

## Status

- ✅ Role/Phase enums, Player/GameState 모델
- ✅ 인원→역할 분배 (4~11명), 승리 조건, 성직자 투표 가중치
- ✅ Night phase (단일/다수 마피아, 두목/부하, 의사, 경찰)
- ✅ Day phase (라운드로빈, 자유 발언)
- ✅ Vote phase (지명, 최후 변론, 찬반)
- ✅ Engine state machine (`setup_game`, `run_game`)
- ✅ E2E tests (시민 승, 마피아 승, 8인 게임)

## Setup

```bash
cd backend
python3.12 -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
```

## Test

```bash
pytest
```

## Lint

```bash
ruff check src tests
ruff format src tests
```

## Next Phase

Phase 2 — Claude Agent 통합. `LLMAgent`가 `PlayerInterface`를 구현해 `MockPlayer`를 교체한다. 페르소나 풀(50), 프롬프트 캐싱, 구조화 출력.
```

- [ ] **Step 2: Commit**

```bash
git add backend/README.md
git commit -m "docs: backend README updated for Phase 1 completion"
```

---

## Self-Review Notes

- **Spec coverage**: 룰(§3.1, §3.2, §3.3, §3.4, §3.5, §3.6), 아키텍처 backend FSM(§4), Player interface(§5.2 메모리), 성직자 비공개 가중치(§3.1 special). LLM·프롬프트·페르소나(§5.1, §5.3, §5.4, §5.5)는 Phase 2 범위로 명시 제외. 웹/WS(§4.1)는 Phase 3 범위. **모두 의도된 분리**.
- **Placeholder scan**: 코드/명령 모든 단계에 실제 내용 포함. TBD 없음.
- **Type consistency**: `target_id`, `text`, `eagerness`, `agree`, `final_target_id`, `vote`, `reasoning` 필드 이름이 MockPlayer 출력과 phase 함수의 사용처에서 일치.
- **Caveats acknowledged inline**:
  - Task 13: `run_day_freetalk`이 Phase 1에서 모든 플레이어에게 eagerness를 묻는 것은 LLM이 아니므로 비용 문제 없음. Phase 2에서는 휴리스틱 + 발언자만 LLM 호출로 변경.
  - Task 9: 부하 반대 시 dialog는 Phase 1에서 1턴(반대 표명 → 두목 최종)으로 단순화. Phase 2에서 2~3턴 주고받기로 확장.
  - Task 4: 10~11명 분배는 spec 9절을 따라 cleric 1개만 포함 (기자/연인 제외).

---

Plan complete and saved to `docs/superpowers/plans/2026-05-23-phase1-backend-game-engine.md`.

**Two execution options:**

**1. Subagent-Driven (recommended)** — I dispatch a fresh subagent per task, review between tasks, fast iteration.

**2. Inline Execution** — Execute tasks in this session using executing-plans, batch execution with checkpoints.

**Which approach?**

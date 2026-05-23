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

# Agentic Mafia Game — Backend (Phase 2 complete)

Phase 2 deliverable: 실제 Claude API로 구동되는 AI 마피아 게임. 50개 페르소나 풀에서 무작위 추출된 캐릭터가 토론·투표·밤 액션을 수행한다. 터미널 CLI로 한 판을 끝까지 관전 가능.

## Status

- ✅ Phase 1: 결정론적 game engine + mock 플레이어 + 59 unit tests
- ✅ Phase 2: ClaudeClient, 50 페르소나 풀, LLMAgent, 액션별 프롬프트, 발언 욕구 휴리스틱, CLI 데모, env-gated 실API e2e
- ⏳ Phase 3: 웹 UI (FastAPI WebSocket + Next.js)

## Setup

```bash
cd backend
python3.12 -m venv .venv      # or `uv venv --python python3.12 .venv`
source .venv/bin/activate
pip install -e ".[dev]"
```

## Run a demo game

```bash
export ANTHROPIC_API_KEY=...
python -m mafia.cli --players 6 --seed 0
```

옵션:
- `--players N` (4~11)
- `--seed S` (재현용)
- `--max-days D` (안전망)

## Test

```bash
pytest                            # 단위/통합 (mock LLM)
ANTHROPIC_API_KEY=... pytest tests/test_e2e_with_api.py    # 실제 API
```

## Lint

```bash
ruff check src tests
ruff format src tests
```

## Cost

Haiku 4.5 + prompt caching 기준 한 판(6명, 약 4 days) 추정 비용 < $0.30. 실제 측정은 `tests/test_e2e_with_api.py` 실행 시 출력 확인.

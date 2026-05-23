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

# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project

Agentic Mafia game: a turn-based mafia/werewolf simulation where every player is an LLM-driven persona. Phase 2 complete (CLI, real Claude API). Phase 3 (FastAPI + Next.js web UI) is planned. All code currently lives under `backend/`.

## Commands

All commands run from `backend/`:

```bash
# Setup (Python 3.12 required)
python3.12 -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"

# Run a demo game (needs API key)
cp .env.example .env && $EDITOR .env            # or `export ANTHROPIC_API_KEY=...`
python -m mafia.cli --players 6 --seed 0        # also: --max-days D

# Tests
pytest                                           # mock-LLM unit/integration (~)
pytest tests/test_engine.py                      # single file
pytest tests/test_engine.py::test_name -v        # single test
ANTHROPIC_API_KEY=... pytest tests/test_e2e_with_api.py   # real API e2e (gated)

# Lint / format
ruff check src tests
ruff format src tests
```

Supported player counts: 4–11 (see `rules.py:_DISTRIBUTION_TABLE`).

## Architecture

The engine is **deterministic and decoupled from the LLM**. `GameEngine` drives a phase state machine and asks `PlayerInterface` implementations for decisions; the interface is satisfied by either `MockPlayer` (tests) or `LLMAgent` (real Claude calls). Tests use `MockPlayer` exclusively, so the entire game flow is exercised without API keys.

Key layers (under `backend/src/mafia/`):

- **`models.py`** — `GameState`, `Player`, `Role`, `Phase`, `Team` dataclasses/enums. `GameState` owns `public_log`, `mafia_log` (mafia-only), `cleric_id` (hidden), `last_night_death`, `winner`. Player private memory (`known_mafia_ids`, `police_investigations`, `doctor_protections`) lives on `Player` and must never leak into prompts for the wrong actor.
- **`engine.py`** — `setup_game` (role assignment, mafia boss designation, cleric hookup) and `run_game` (the state-machine loop). Day-first ordering: `DAY_ROUNDROBIN → DAY_FREETALK → VOTE_NOMINATE → (LAST_WORDS → VOTE_UPDOWN) → check_winner → NIGHT → check_winner`. Day 1 has no prior night.
- **`phases/`** — one module per phase (`day.py`, `night.py`, `vote.py`). Each function takes `(state, actors)` and mutates `state`. Night handles mafia chat among allies, boss propose / underling respond / boss final dialog, then doctor protect and police investigate.
- **`rules.py`** — role distribution table and `check_winner` (mafia wins when `len(alive_mafia) >= len(alive_citizens)`). `vote_weight` gives the cleric 2 votes.
- **`player.py`** — `PlayerInterface` protocol with one method, `decide(DecisionContext) -> dict`. `DecisionContext.action` is a string key like `"speak_turn"`, `"vote_nominate"`, `"night_kill"`, `"night_boss_propose"`, `"freetalk_eagerness"`. `MockPlayer` accepts a scripted dict keyed by action; see its docstring for the per-action return shape — tests rely on this contract.
- **`agents/`** — LLM side. `personas.json` (50 personas, packaged via `package-data`), `personas.py` (pool + draw), `prompts.py` (system + per-action user prompts), `eagerness.py` (deterministic heuristic for free-talk turn-taking, not an LLM call), `llm_agent.py` (`LLMAgent` glues persona + prompts + `ClaudeClient`; on `LLMError` falls back to safe defaults from `_FALLBACK_ANSWERS`).
- **`llm/claude_client.py`** — Anthropic SDK wrapper. Default model is `claude-haiku-4-5-20251001`. System prompt is sent with `cache_control: ephemeral` so repeated calls within the 5-minute cache window hit prompt cache (this is core to keeping cost < ~$0.30/game). `complete_json` retries up to 2× and strips ```json fences before parsing; if parsing still fails it raises `LLMError`, which `LLMAgent` converts to a fallback.
- **`cli.py`** — terminal driver. Pairs each `Player` with a drawn `Persona` (renames `player.name` to the persona name) and prints the run with `rich`.

## Conventions worth knowing

- `Role.CLERIC` is hidden from everyone except the cleric; `GameState.cleric_id` is the only canonical place to check. The cleric gets 2 votes but reveals nothing on death.
- On death, role is revealed publicly **only if mafia**; citizen roles stay hidden (see `21eba7c`).
- Each player speaks at most once per free-talk phase (`5158d74`).
- Round-robin is one pass per day (`ff5784c` reverted multi-pass).
- When adding a new action key, update `MockPlayer.decide` shape handling, `LLMAgent._validate`, prompts in `agents/prompts.py`, and the relevant phase caller — all four must agree.
- `personas.json` is package data; if you add fields, also update `setuptools.package-data` is already wired but reinstall (`pip install -e .`) after edits.

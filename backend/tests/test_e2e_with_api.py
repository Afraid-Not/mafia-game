"""Real-API e2e smoke test. Skipped unless ANTHROPIC_API_KEY is set."""
import os
import random

import pytest

from mafia.cli import build_agents_for_state, run_demo
from mafia.engine import run_game, setup_game
from mafia.llm.claude_client import ClaudeClient
from mafia.models import Phase

pytestmark = pytest.mark.skipif(
    not os.environ.get("ANTHROPIC_API_KEY"),
    reason="ANTHROPIC_API_KEY not set — skipping real-API e2e",
)


def test_real_api_4player_game_terminates():
    client = ClaudeClient(max_tokens=300)
    rng = random.Random(2026)
    state = setup_game(player_count=4, rng=rng)
    actors = build_agents_for_state(state, client=client, rng=rng)
    winner = run_game(state, actors, max_days=10)
    assert state.phase == Phase.GAME_OVER
    assert winner in {"mafia", "citizen", "draw"}

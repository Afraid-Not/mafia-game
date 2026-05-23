"""Speech-eagerness heuristic — no LLM call.

Score components (per spec §5.4):
- 최근 자기 이름 언급됨: +3 (마지막 2 라운드)
- 마지막 발언 이후 경과 라운드: +N
- 자신이 투표 후보로 거론됨: +4 per vote
- 자기 역할로 알려줘야 할 새 정보 있음: handled elsewhere (police results)
- 페르소나 외향성 가중치: optional ±2 (caller can pass)
"""

from __future__ import annotations

from mafia.models import GameState

_NAME_MENTION_LOOKBACK_TURNS = 6  # last 2 logical rounds ≈ 6 entries (rough)
_NAME_MENTION_BONUS = 3
_VOTE_AGAINST_BONUS = 2  # per vote received in last vote_nominate phase
_SILENCE_BONUS_PER_TURN = 1


def _entries_since_actor_spoke(state: GameState, actor_id: str) -> int:
    """Count public-log entries appended since actor's last speak/freetalk."""
    speak_indices = [
        i
        for i, e in enumerate(state.public_log)
        if e.get("kind") in {"speak", "speak_freetalk"} and e.get("speaker_id") == actor_id
    ]
    if not speak_indices:
        return len(state.public_log)
    return len(state.public_log) - speak_indices[-1] - 1


def _name_mention_count(state: GameState, actor_id: str) -> int:
    actor = state.player_by_id(actor_id) if any(p.id == actor_id for p in state.players) else None
    if actor is None:
        return 0
    recent = state.public_log[-_NAME_MENTION_LOOKBACK_TURNS:]
    needle = actor.name
    return sum(
        1
        for e in recent
        if needle and needle in str(e.get("text", "")) and e.get("speaker_id") != actor_id
    )


def _votes_against(state: GameState, actor_id: str) -> int:
    return sum(
        1
        for e in state.public_log
        if e.get("kind") == "vote_nominate" and e.get("target_id") == actor_id
    )


def compute_eagerness(state: GameState, actor_id: str, extraversion: int = 0) -> int:
    score = 0
    score += _NAME_MENTION_BONUS * _name_mention_count(state, actor_id)
    score += _SILENCE_BONUS_PER_TURN * _entries_since_actor_spoke(state, actor_id)
    score += _VOTE_AGAINST_BONUS * _votes_against(state, actor_id)
    score += extraversion
    return max(0, score)

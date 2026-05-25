"""Speech-eagerness heuristic — no LLM call.

Score components (per spec §5.4):
- 최근 자기 이름 언급됨: +3 (마지막 2 라운드)
- 마지막 발언 이후 경과 라운드: +N
- 자신이 투표 후보로 거론됨: +4 per vote
- 경찰: 아직 공개하지 않은 마피아 확정 정보가 있음 → +5
- 의사: 직전 밤 보호가 성공(night_safe)했음 → +3
- 페르소나 외향성 가중치: optional ±2 (caller can pass)
"""

from __future__ import annotations

from mafia.models import GameState, Role

_NAME_MENTION_LOOKBACK_TURNS = 6  # last 2 logical rounds ≈ 6 entries (rough)
_NAME_MENTION_BONUS = 3
_VOTE_AGAINST_BONUS = 2  # per vote received in last vote_nominate phase
_SILENCE_BONUS_PER_TURN = 1
_POLICE_HOT_INFO_BONUS = 5
_DOCTOR_SAVE_BONUS = 3


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


def _police_has_undisclosed_mafia_hit(state: GameState, actor_id: str) -> bool:
    """Returns True if this actor is a police with a confirmed-mafia investigation
    result that has not yet been mentioned in any of their public speeches."""
    actor = next((p for p in state.players if p.id == actor_id), None)
    if actor is None or actor.role != Role.POLICE:
        return False
    mafia_hits = [tid for tid, is_m in actor.police_investigations if is_m]
    if not mafia_hits:
        return False
    own_speech_text = " ".join(
        str(e.get("text", ""))
        for e in state.public_log
        if e.get("kind") in {"speak", "speak_freetalk"} and e.get("speaker_id") == actor_id
    )
    for tid in mafia_hits:
        hit = next((p for p in state.players if p.id == tid), None)
        if hit is None:
            continue
        if hit.name not in own_speech_text and tid not in own_speech_text:
            return True
    return False


def _doctor_just_saved(state: GameState, actor_id: str) -> bool:
    """Returns True if this actor is a doctor and the most recent night ended
    in night_safe (mafia targeted someone but doctor protected). The bonus
    decays after the doctor has spoken once since the save."""
    actor = next((p for p in state.players if p.id == actor_id), None)
    if actor is None or actor.role != Role.DOCTOR:
        return False
    last_night_idx = -1
    for i, e in enumerate(state.public_log):
        if e.get("kind") in {"night_safe", "night_death"}:
            last_night_idx = i
    if last_night_idx == -1:
        return False
    last_night = state.public_log[last_night_idx]
    if last_night.get("kind") != "night_safe":
        return False
    # Has the doctor already spoken since the save?
    for e in state.public_log[last_night_idx + 1 :]:
        if e.get("kind") in {"speak", "speak_freetalk"} and e.get("speaker_id") == actor_id:
            return False
    return True


def compute_eagerness(state: GameState, actor_id: str, extraversion: int = 0) -> int:
    score = 0
    score += _NAME_MENTION_BONUS * _name_mention_count(state, actor_id)
    score += _SILENCE_BONUS_PER_TURN * _entries_since_actor_spoke(state, actor_id)
    score += _VOTE_AGAINST_BONUS * _votes_against(state, actor_id)
    if _police_has_undisclosed_mafia_hit(state, actor_id):
        score += _POLICE_HOT_INFO_BONUS
    if _doctor_just_saved(state, actor_id):
        score += _DOCTOR_SAVE_BONUS
    score += extraversion
    return max(0, score)

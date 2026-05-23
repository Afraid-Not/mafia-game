"""Prompt builders. System prompt is cached per (game, actor). User prompt is per-call."""

from __future__ import annotations

from mafia.agents.personas import Persona
from mafia.models import GameState, Player, Role

_ROLE_DESCRIPTIONS_KO = {
    Role.CIVILIAN: "시민. 능력 없음. 토론과 투표로 마피아를 찾아내야 함.",
    Role.POLICE: "경찰. 매일 밤 1명을 조사해 마피아 여부를 비공개로 확인.",
    Role.DOCTOR: "의사. 매일 밤 1명을 보호하면 마피아의 타겟이 일치할 경우 생존.",
    Role.MAFIA: "마피아. 시민을 죽이고 자신의 정체를 숨겨야 함.",
    Role.CLERIC: "성직자. 시민측이지만 투표 시 2표를 행사 (정체는 비공개).",
}

SYSTEM_PROMPT_TEMPLATE = """당신은 '{persona_name}'이라는 캐릭터로 마피아 게임을 플레이합니다.

## 페르소나
- 이름: {persona_name}
- 직업: {persona_job}
- 성격: {persona_personality}
- 말투 예시: "{persona_style}"

이 페르소나의 성격과 말투를 일관되게 유지하세요. 발언은 짧고 자연스럽게.

**언어 규칙**: 모든 발언·이유(reasoning)·텍스트 필드는 반드시 **한국어로만** 작성하세요.
영어 단어·문장 사용 금지. 외래어는 한글 표기로 (예: "패턴" ✓, "pattern" ✗).

## 당신의 게임 내 역할
{role_description}
{role_extra}

## 게임 규칙 요약
- 인원: {n_players}명. 마피아와 시민이 섞여 있음.
- 매일 밤 마피아는 1명을 죽이고, 의사·경찰이 능력 사용.
- 매일 낮 토론 → 1차 투표(처형 후보) → 후보의 최후 변론 → 찬반 투표.
- 시민 승: 마피아 전원 사망 / 마피아 승: 마피아 수 ≥ 시민 수.
- 거짓말·연기·추리·설득이 모두 허용.

## 출력 형식
요청된 액션에 따라 지정된 JSON 형식으로만 응답하세요. 다른 설명이나 코드펜스 없이 JSON만.
"""


def _role_extra(actor: Player) -> str:
    extra: list[str] = []
    if actor.role == Role.MAFIA:
        allies = [m for m in actor.known_mafia_ids if m]
        if allies:
            extra.append(f"동료 마피아: {', '.join(allies)}")
        if actor.is_mafia_boss:
            extra.append("당신은 마피아 두목입니다. 밤마다 타겟을 먼저 지명합니다.")
        else:
            extra.append("당신은 마피아 부하입니다. 두목 제안에 동의/반대를 선택합니다.")
    if actor.role == Role.POLICE and actor.police_investigations:
        results = ", ".join(
            f"{tid}={'마피아' if is_m else '시민'}" for tid, is_m in actor.police_investigations
        )
        extra.append(f"이전 조사 결과: {results}")
    if actor.role == Role.DOCTOR and actor.doctor_protections:
        extra.append(f"이전 보호 이력: {', '.join(actor.doctor_protections)}")
    return "\n".join(extra)


def build_system_prompt(*, state: GameState, actor: Player, persona: Persona) -> str:
    return SYSTEM_PROMPT_TEMPLATE.format(
        persona_name=persona.name,
        persona_job=persona.job,
        persona_personality=persona.personality,
        persona_style=persona.style,
        role_description=_ROLE_DESCRIPTIONS_KO[actor.role],
        role_extra=_role_extra(actor),
        n_players=len(state.players),
    )


def _format_public_log(state: GameState, max_entries: int = 60) -> str:
    lines: list[str] = []
    for e in state.public_log[-max_entries:]:
        kind = e.get("kind", "?")
        if kind == "speak":
            speaker = state.player_by_id(e["speaker_id"]).name
            lines.append(f"[발언] {speaker}: {e.get('text', '')}")
        elif kind == "speak_freetalk":
            speaker = state.player_by_id(e["speaker_id"]).name
            lines.append(f"[자유발언] {speaker}: {e.get('text', '')}")
        elif kind == "vote_nominate":
            voter = state.player_by_id(e["voter_id"]).name
            target = (
                state.player_by_id(e["target_id"]).name
                if any(p.id == e["target_id"] for p in state.players)
                else e["target_id"]
            )
            lines.append(f"[지명투표] {voter} → {target}")
        elif kind == "vote_updown":
            voter = state.player_by_id(e["voter_id"]).name
            lines.append(f"[찬반] {voter}: {e.get('vote', '?')}")
        elif kind == "execution":
            target = state.player_by_id(e["candidate_id"]).name
            role = e.get("role", "?")
            lines.append(
                f"[처형] {target} — 역할 [{role}] "
                f"(찬성 {e.get('yes', '?')}, 반대 {e.get('no', '?')})"
            )
        elif kind == "pardon":
            target = state.player_by_id(e["candidate_id"]).name
            lines.append(
                f"[무죄 방면] {target} (찬성 {e.get('yes', '?')}, 반대 {e.get('no', '?')})"
            )
        elif kind == "night_death":
            target = state.player_by_id(e["victim_id"]).name
            role = e.get("victim_role", "?")
            lines.append(f"[밤 사망] {target} — 역할 [{role}]")
        elif kind == "night_safe":
            lines.append("[밤 결과] 아무도 죽지 않음 (의사 보호 성공)")
        elif kind == "last_words":
            target = state.player_by_id(e["speaker_id"]).name
            lines.append(f"[최후변론] {target}: {e.get('text', '')}")
        else:
            lines.append(f"[{kind}] {e}")
    return "\n".join(lines) if lines else "(아직 발언 없음)"


def _alive_others(state: GameState, actor: Player) -> list[Player]:
    return [p for p in state.alive_players() if p.id != actor.id]


def _candidates_list(state: GameState, actor: Player) -> str:
    return ", ".join(f"{p.id}({p.name})" for p in _alive_others(state, actor))


def build_user_prompt(*, state: GameState, actor: Player, action: str, payload: dict) -> str:
    log = _format_public_log(state)
    base = f"## 지금까지 공개 로그 (Day {state.day_number})\n{log}\n\n"

    if action == "speak_turn":
        return base + (
            '지금은 낮 토론의 당신 차례입니다 (speak_turn).\n{"text": "당신의 발언 (1~3문장)"}'
        )

    if action == "speak_freetalk":
        return base + ('자유 발언 차례입니다 (speak_freetalk).\n{"text": "발언"}')

    if action == "last_words":
        return base + (
            '당신이 처형 후보로 지명되었습니다. 최후 변론을 하세요.\n{"text": "최후 변론"}'
        )

    if action == "vote_nominate":
        candidates = _candidates_list(state, actor)
        return base + (
            f"1차 투표: 처형하고 싶은 사람 1명을 지목하세요.\n"
            f"후보: {candidates}\n"
            '{"target_id": "p_X", "reasoning": "이유"}'
        )

    if action == "vote_updown":
        cand_id = payload["candidate_id"]
        cand_name = state.player_by_id(cand_id).name
        return base + (
            f"후보 {cand_id}({cand_name})를 처형할지 찬반 투표합니다.\n"
            '{"vote": "yes" 또는 "no", "reasoning": "이유"}'
        )

    if action == "night_kill":
        candidates = _candidates_list(state, actor)
        return base + (
            f"밤이 되었습니다. 마피아인 당신이 죽일 타겟을 고르세요.\n"
            f"후보: {candidates}\n"
            '{"target_id": "p_X", "reasoning": "이유"}'
        )

    if action == "night_boss_propose":
        candidates = _candidates_list(state, actor)
        return base + (
            f"두목인 당신이 오늘 밤 타겟을 부하들에게 제안합니다.\n"
            f"후보: {candidates}\n"
            '{"target_id": "p_X", "reasoning": "이유", "text": "단톡 발언"}'
        )

    if action == "night_underling_respond":
        proposed = payload.get("proposed_target_id")
        return base + (
            f"두목이 {proposed} 처형을 제안했습니다. 동의하시겠습니까?\n"
            '{"agree": "yes" 또는 "no", "reasoning": "이유", "text": "단톡 발언"}'
        )

    if action == "night_boss_dialog":
        proposed = payload.get("proposed_target_id")
        dissenters = payload.get("dissenters", [])
        return base + (
            f"부하 {dissenters}가 {proposed} 처형에 반대했습니다. 최종 결정을 내리세요.\n"
            '{"text": "최종 발언", "final_target_id": "p_X 또는 null로 원래 타겟 유지"}'
        )

    if action == "night_doctor_protect":
        return base + (
            f"의사인 당신이 오늘 밤 보호할 사람을 고르세요 (자신 포함 가능).\n"
            f"후보: {_candidates_list(state, actor)}, {actor.id}({actor.name})\n"
            '{"target_id": "p_X", "reasoning": "이유"}'
        )

    if action == "night_police_investigate":
        return base + (
            f"경찰인 당신이 오늘 밤 조사할 사람을 고르세요.\n"
            f"후보: {_candidates_list(state, actor)}\n"
            '{"target_id": "p_X", "reasoning": "이유"}'
        )

    if action == "mafia_chat":
        return base + 'JSON으로 마피아 단톡 발언: {"text": "..."}'

    raise ValueError(f"unknown action for prompt: {action}")

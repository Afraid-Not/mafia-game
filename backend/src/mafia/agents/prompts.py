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
            role = e.get("role")
            day = e.get("day_number", "?")
            role_label = f"실제 역할: {role}" if role else "역할: 비공개 (마피아가 아님)"
            lines.append(
                f"[Day {day} 낮 — 시민 투표로 처형] {target} "
                f"({role_label}, 찬성 {e.get('yes', '?')} 반대 {e.get('no', '?')})"
            )
        elif kind == "pardon":
            target = state.player_by_id(e["candidate_id"]).name
            day = e.get("day_number", "?")
            lines.append(
                f"[Day {day} 낮 — 처형 부결, 생존] {target} "
                f"(찬성 {e.get('yes', '?')} 반대 {e.get('no', '?')})"
            )
        elif kind == "night_death":
            target = state.player_by_id(e["victim_id"]).name
            role = e.get("victim_role")
            day = e.get("day_number", "?")
            role_label = f"실제 역할: {role}" if role else "역할: 비공개 (마피아가 아님)"
            lines.append(f"[Day {day} 밤 — 마피아 살해] {target} ({role_label})")
        elif kind == "night_safe":
            day = e.get("day_number", "?")
            lines.append(
                f"[Day {day} 밤 — 의사 보호 성공] 마피아가 누군가를 노렸으나 "
                "의사의 보호로 그 타겟이 생존. 사망자 없음. "
                "**확정 사실**: 의사가 살아 있고 보호에 성공했음. "
                "논점은 '의사가 보호한 대상이 누구인지', '그게 곧 마피아의 다음 타겟임'."
            )
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


def _player_name(state: GameState, pid: str) -> str:
    return next((p.name for p in state.players if p.id == pid), pid)


def _speak_strategy_hint(state: GameState, actor: Player) -> str:
    """Role-aware guidance: forces commitment to suspicion/claim instead of pure observation."""
    if state.day_number == 1:
        return (
            "**첫날 발언 안내**: 자기소개 후 페르소나 말투에 맞게 "
            "**신경 쓰이는 사람 한 명**(긍정/부정 무관)을 짧게 짚으세요. "
            "단순 관찰·메타 코멘트('지켜보자', '정보가 부족하다')는 금지. "
            "능력 공개는 아직 줄 정보가 없으니 보류."
        )

    common = (
        "**발언 안내**: 단순 정리·관찰('지켜보자', '정보가 부족하다')은 **금지**. "
        "다음 중 하나 이상을 반드시 포함하세요:\n"
        "- 가장 의심스러운 1명 + 행동적 근거(어떤 발언/투표 패턴 때문인지)\n"
        "- 또는 가장 신뢰하는 1명 + 그 이유\n"
        "- 또는 본인/타인의 역할 클레임(진실 또는 거짓)"
    )

    if actor.role == Role.POLICE and actor.police_investigations:
        last_tid, last_is_m = actor.police_investigations[-1]
        last_name = _player_name(state, last_tid)
        verdict = "마피아" if last_is_m else "시민"
        role_line = (
            f"**경찰 전략**: 가장 최근 조사 결과 = {last_name}({verdict}). "
            "공개하면 시민이 결집되지만 다음 밤 1순위 타겟이 됩니다. "
            "공개·은닉·시점은 당신의 전략적 판단."
        )
    elif actor.role == Role.DOCTOR and actor.doctor_protections:
        last_pid = actor.doctor_protections[-1]
        last_name = _player_name(state, last_pid)
        role_line = (
            f"**의사 전략**: 가장 최근 보호 = {last_name}. "
            "보호가 성공했다면 '내가 살렸다'고 클레임해 신뢰를 얻을 수 있으나 "
            "다음 밤 타겟이 됩니다. 거짓 보호 클레임도 가능."
        )
    elif actor.role == Role.MAFIA:
        role_line = (
            "**마피아 전략**: 시민/경찰/의사 행세로 시선을 분산하세요. "
            "진짜 경찰이 등장하면 카운터 클레임(가짜 경찰)으로 혼란 유도. "
            "동료 마피아를 과하게 옹호하지 말고, 가끔은 의심하는 척도 효과적."
        )
    elif actor.role == Role.CLERIC:
        role_line = (
            "**성직자 전략**: 정체는 절대 노출 금지(2표의 가치는 비공개일 때만). "
            "평범한 시민처럼 토론에 참여하세요."
        )
    elif actor.role == Role.CIVILIAN:
        role_line = (
            "**시민 전략**: 능력은 없지만, 의사·경찰 행세로 마피아를 흔들거나 "
            "진짜 능력자 클레임을 검증·증폭할 수 있습니다."
        )
    else:
        role_line = ""

    return common + ("\n" + role_line if role_line else "")


def _freetalk_hint(state: GameState) -> str:
    if state.day_number == 1:
        return (
            "**자유발언 안내**: 직전 발언 중 하나에 **이름을 명시해** 직접 반응하세요"
            "(동의/반박/질문). 단순 정리·메타 멘트 금지."
        )
    return (
        "**자유발언 안내**: 직전 발언자 중 한 명을 **이름으로 직접 거론**하며 "
        "동의·반박·질문하세요. 누군가의 역할 클레임이 있었다면 "
        "검증·동조·카운터 클레임을 고려하세요. 단순 정리·관찰 멘트 금지."
    )


def _roster_line(state: GameState) -> str:
    alive = ", ".join(f"{p.id}({p.name})" for p in state.alive_players())
    return (
        f"## 생존자 (반드시 이 명단의 실제 ID/이름만 사용. 존재하지 않는 번호나 이름을 "
        f"만들어내지 마세요)\n{alive}\n\n"
    )


def build_user_prompt(*, state: GameState, actor: Player, action: str, payload: dict) -> str:
    log = _format_public_log(state)
    day_note = ""
    if state.day_number == 1:
        day_note = (
            "**상황 안내**: 지금은 첫째 날 아침입니다. **아직 밤이 한 번도 지나지 않았으므로**\n"
            "사망자는 없으며, 누가 누구를 죽였는지에 대한 정보가 전혀 없습니다.\n"
            '"어젯밤" "누가 죽었어" 같은 표현은 사용하지 마세요.\n\n'
        )
    roster = _roster_line(state)
    base = f"{day_note}{roster}## 지금까지 공개 로그 (Day {state.day_number})\n{log}\n\n"

    if action == "speak_turn":
        hint = _speak_strategy_hint(state, actor)
        return base + (
            f"{hint}\n\n"
            "지금은 낮 토론의 당신 차례입니다 (speak_turn). "
            "다른 플레이어를 지목할 때는 위 생존자 명단의 **정확한 이름**을 사용하세요. "
            '페르소나 말투를 유지하며 1~3문장.\n{"text": "당신의 발언"}'
        )

    if action == "speak_freetalk":
        hint = _freetalk_hint(state)
        return base + (
            f"{hint}\n\n"
            "자유 발언 차례입니다 (speak_freetalk). 위 생존자 명단의 **정확한 이름**만 "
            '거론하세요. 1~3문장.\n{"text": "발언"}'
        )

    if action == "last_words":
        return base + (
            '당신이 처형 후보로 지명되었습니다. 최후 변론을 하세요.\n{"text": "최후 변론"}'
        )

    if action == "vote_nominate":
        candidates = _candidates_list(state, actor)
        nudge = ""
        if actor.role == Role.POLICE:
            mafia_hits = [
                _player_name(state, tid)
                for tid, is_m in actor.police_investigations
                if is_m and any(p.id == tid and p.alive for p in state.players)
            ]
            if mafia_hits:
                names = ", ".join(mafia_hits)
                nudge = (
                    f"**경찰 환기**: 당신은 {names}이(가) 마피아임을 직접 확인했습니다. "
                    "일반적으로 이 정보를 우선시해 그 대상을 지목하는 것이 시민 승리에 유리합니다 "
                    "(분위기에 휩쓸려 다른 사람을 지목하지 마세요).\n"
                )
        elif actor.role == Role.MAFIA and actor.known_mafia_ids:
            allies = ", ".join(
                _player_name(state, mid)
                for mid in actor.known_mafia_ids
                if any(p.id == mid and p.alive for p in state.players)
            )
            if allies:
                nudge = (
                    f"**마피아 환기**: 동료({allies})를 절대 지목하지 마세요. "
                    "능력자(경찰·의사로 의심되는 시민)나 영향력 큰 시민을 노리는 게 유리합니다.\n"
                )
        return base + (
            f"{nudge}"
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

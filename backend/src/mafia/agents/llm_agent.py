"""LLMAgent: a PlayerInterface backed by Claude API."""

from __future__ import annotations

from typing import Any

from mafia.agents.eagerness import compute_eagerness
from mafia.agents.personas import Persona
from mafia.agents.prompts import build_system_prompt, build_user_prompt
from mafia.llm.claude_client import ClaudeClient, LLMError
from mafia.models import Player
from mafia.player import DecisionContext

_FALLBACK_ANSWERS: dict[str, dict[str, Any]] = {
    "speak_turn": {"text": "..."},
    "speak_freetalk": {"text": "..."},
    "last_words": {"text": "..."},
    "mafia_chat": {"text": "..."},
    "vote_updown": {"vote": "no", "reasoning": "fallback"},
}

_HEURISTIC_ACTIONS = {"freetalk_eagerness"}


class LLMAgent:
    """PlayerInterface impl that calls Claude. Stateless w.r.t. game logic — engine owns state."""

    def __init__(self, *, actor: Player, persona: Persona, client: ClaudeClient):
        self._actor = actor
        self._persona = persona
        self._client = client

    def decide(self, ctx: DecisionContext) -> dict[str, Any]:
        if ctx.action in _HEURISTIC_ACTIONS:
            return self._heuristic(ctx)
        return self._llm(ctx)

    def _heuristic(self, ctx: DecisionContext) -> dict[str, Any]:
        if ctx.action == "freetalk_eagerness":
            score = compute_eagerness(ctx.state, self._actor.id)
            return {"eagerness": score}
        raise ValueError(f"no heuristic for action {ctx.action}")

    def _llm(self, ctx: DecisionContext) -> dict[str, Any]:
        import json as _json

        system = build_system_prompt(state=ctx.state, actor=self._actor, persona=self._persona)
        user = build_user_prompt(
            state=ctx.state, actor=self._actor, action=ctx.action, payload=ctx.payload
        )
        try:
            raw = self._client.complete_json(system=system, user=user)
        except LLMError:
            return self._fallback(ctx)
        # complete_json may return a real dict (from ClaudeClient) or a mock (in tests).
        # If the result is not a plain dict, try to extract text from complete() instead.
        if not isinstance(raw, dict):
            try:
                resp = self._client.complete(system=system, user=user)
                text = resp.text if hasattr(resp, "text") else str(resp)
                raw = _json.loads(text)
            except Exception:
                return self._fallback(ctx)
        return self._validate(ctx, raw)

    def _validate(self, ctx: DecisionContext, raw: dict[str, Any]) -> dict[str, Any]:
        alive_ids = {p.id for p in ctx.state.alive_players()}
        non_self_alive = alive_ids - {self._actor.id}

        if ctx.action in {"vote_nominate", "night_kill", "night_police_investigate"}:
            target = raw.get("target_id")
            if target not in non_self_alive:
                target = next(iter(sorted(non_self_alive)), self._actor.id)
            return {"target_id": target, "reasoning": str(raw.get("reasoning", ""))}

        if ctx.action == "night_doctor_protect":
            target = raw.get("target_id")
            if target not in alive_ids:
                target = self._actor.id  # default: self-protect
            return {"target_id": target, "reasoning": str(raw.get("reasoning", ""))}

        if ctx.action == "vote_updown":
            vote = raw.get("vote", "").lower()
            if vote not in {"yes", "no"}:
                vote = "no"
            return {"vote": vote, "reasoning": str(raw.get("reasoning", ""))}

        if ctx.action == "night_boss_propose":
            target = raw.get("target_id")
            if target not in non_self_alive:
                target = next(iter(sorted(non_self_alive)), self._actor.id)
            return {
                "target_id": target,
                "reasoning": str(raw.get("reasoning", "")),
                "text": str(raw.get("text", "")),
            }

        if ctx.action == "night_underling_respond":
            agree = raw.get("agree", "").lower()
            if agree not in {"yes", "no"}:
                agree = "yes"
            return {
                "agree": agree,
                "reasoning": str(raw.get("reasoning", "")),
                "text": str(raw.get("text", "")),
            }

        if ctx.action == "night_boss_dialog":
            final = raw.get("final_target_id")
            if final is not None and final not in non_self_alive:
                final = None  # keep original proposed_target
            return {"text": str(raw.get("text", "")), "final_target_id": final}

        if ctx.action in {"speak_turn", "speak_freetalk", "last_words", "mafia_chat"}:
            return {"text": str(raw.get("text", "..."))}

        raise ValueError(f"unknown action: {ctx.action}")

    def _fallback(self, ctx: DecisionContext) -> dict[str, Any]:
        if ctx.action in _FALLBACK_ANSWERS:
            return _FALLBACK_ANSWERS[ctx.action]
        # For target-style actions, snap to first alive non-self
        alive_others = sorted(p.id for p in ctx.state.alive_players() if p.id != self._actor.id)
        if alive_others:
            target = alive_others[0]
            if ctx.action == "night_boss_propose":
                return {"target_id": target, "reasoning": "fallback", "text": "..."}
            if ctx.action == "night_underling_respond":
                return {"agree": "yes", "reasoning": "fallback", "text": "..."}
            if ctx.action == "night_boss_dialog":
                return {"text": "...", "final_target_id": None}
            return {"target_id": target, "reasoning": "fallback"}
        return {"target_id": self._actor.id, "reasoning": "fallback"}

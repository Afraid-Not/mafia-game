"""Player interface: protocol all decision-makers (mock or LLM) implement."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Protocol

from mafia.models import GameState


@dataclass
class DecisionContext:
    """Everything a player needs to make a decision for one action."""

    state: GameState
    actor_id: str
    action: str  # e.g. "speak_turn", "vote_nominate", "night_kill", ...
    payload: dict[str, Any] = field(default_factory=dict)


class PlayerInterface(Protocol):
    """Anything that can make decisions for a Player implements this."""

    def decide(self, ctx: DecisionContext) -> dict[str, Any]: ...


class MockPlayer:
    """Returns scripted responses keyed by action name.

    For `speak_turn`, `last_words`: scripted value is a str → wrapped as {"text": ...}.
    For `vote_nominate`, `vote_updown`, `night_kill`, `night_doctor_protect`,
      `night_police_investigate`, `night_boss_propose`, `night_underling_respond`,
      `night_boss_dialog`, `mafia_chat`: scripted value is the target id or a dict.
    For `freetalk_eagerness`: scripted value is an int → wrapped as {"eagerness": int}.
    For `speak_freetalk`: scripted value is a str → wrapped as {"text": str}.
    """

    def __init__(self, scripted: dict[str, Any]):
        self._scripted = scripted

    def decide(self, ctx: DecisionContext) -> dict[str, Any]:
        if ctx.action not in self._scripted:
            raise KeyError(f"MockPlayer has no scripted response for action={ctx.action}")
        raw = self._scripted[ctx.action]

        if ctx.action in ("speak_turn", "last_words", "mafia_chat"):
            return {"text": raw if isinstance(raw, str) else raw["text"]}

        if ctx.action == "freetalk_eagerness":
            if isinstance(raw, int):
                return {"eagerness": raw}
            return raw  # already dict

        if ctx.action == "speak_freetalk":
            if isinstance(raw, str):
                return {"text": raw}
            # legacy dict form {"eagerness", "text"} — return text only
            if isinstance(raw, dict) and "text" in raw:
                return {"text": raw["text"]}
            return raw

        if ctx.action in (
            "vote_nominate",
            "night_kill",
            "night_doctor_protect",
            "night_police_investigate",
        ):
            if isinstance(raw, str):
                return {"target_id": raw, "reasoning": "mock"}
            return raw

        if ctx.action == "vote_updown":
            if isinstance(raw, str):
                return {"vote": raw, "reasoning": "mock"}
            return raw

        if ctx.action == "night_boss_propose":
            if isinstance(raw, str):
                return {"target_id": raw, "reasoning": "mock", "text": f"오늘은 {raw}"}
            return raw

        if ctx.action == "night_underling_respond":
            if isinstance(raw, str):
                return {"agree": raw, "reasoning": "mock", "text": ""}
            return raw

        if ctx.action == "night_boss_dialog":
            return raw if isinstance(raw, dict) else {"text": raw, "final_target_id": None}

        # Fallback: return raw as-is if it's a dict
        if isinstance(raw, dict):
            return raw
        raise ValueError(f"unhandled mock action {ctx.action} with raw={raw!r}")

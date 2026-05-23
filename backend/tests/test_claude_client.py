import json
from unittest.mock import MagicMock

import pytest

from mafia.llm.claude_client import ClaudeClient, LLMError


def _fake_response_with_text(text: str) -> MagicMock:
    """Build a fake anthropic SDK Message object whose content[0].text is `text`."""
    msg = MagicMock()
    block = MagicMock()
    block.text = text
    msg.content = [block]
    msg.usage = MagicMock()
    msg.usage.input_tokens = 100
    msg.usage.output_tokens = 50
    return msg


def test_complete_returns_text():
    fake_sdk = MagicMock()
    fake_sdk.messages.create.return_value = _fake_response_with_text("hello world")
    client = ClaudeClient(sdk=fake_sdk, model="claude-haiku-4-5-20251001")
    result = client.complete(system="You are a helper.", user="Say hi.")
    assert result.text == "hello world"
    assert result.input_tokens == 100
    assert result.output_tokens == 50


def test_complete_uses_cache_control_on_system():
    fake_sdk = MagicMock()
    fake_sdk.messages.create.return_value = _fake_response_with_text("ok")
    client = ClaudeClient(sdk=fake_sdk, model="claude-haiku-4-5-20251001")
    client.complete(system="long system prompt", user="hi")
    call = fake_sdk.messages.create.call_args
    system_arg = call.kwargs["system"]
    # System should be passed as a list of blocks with cache_control on the last block
    assert isinstance(system_arg, list)
    assert system_arg[-1].get("cache_control") == {"type": "ephemeral"}


def test_complete_json_parses_response():
    payload = {"target_id": "p2", "reasoning": "suspicious"}
    fake_sdk = MagicMock()
    fake_sdk.messages.create.return_value = _fake_response_with_text(json.dumps(payload))
    client = ClaudeClient(sdk=fake_sdk, model="claude-haiku-4-5-20251001")
    result = client.complete_json(system="sys", user="usr")
    assert result == payload


def test_complete_json_extracts_from_codefence():
    payload = {"vote": "yes", "reasoning": "obvious"}
    fenced = f"```json\n{json.dumps(payload)}\n```"
    fake_sdk = MagicMock()
    fake_sdk.messages.create.return_value = _fake_response_with_text(fenced)
    client = ClaudeClient(sdk=fake_sdk, model="claude-haiku-4-5-20251001")
    result = client.complete_json(system="sys", user="usr")
    assert result == payload


def test_complete_json_retries_on_parse_failure_then_raises():
    fake_sdk = MagicMock()
    fake_sdk.messages.create.return_value = _fake_response_with_text("not json at all")
    client = ClaudeClient(sdk=fake_sdk, model="claude-haiku-4-5-20251001", max_json_retries=2)
    with pytest.raises(LLMError):
        client.complete_json(system="sys", user="usr")
    assert fake_sdk.messages.create.call_count == 2

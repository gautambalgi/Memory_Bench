import asyncio
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from memorybench.agent.providers import OpenAIProvider


def test_live_provider_requires_key(settings):
    with pytest.raises(ValueError, match="OPENAI_API_KEY"):
        OpenAIProvider(settings)


def test_live_adapter_preserves_continuation_and_tools(settings):
    from pydantic import SecretStr

    settings.api_key = SecretStr("test-key")
    item = SimpleNamespace(
        type="function_call", call_id="c1", name="calculate", arguments='{"expression":"2+2"}'
    )
    raw = {
        "type": "function_call",
        "call_id": "c1",
        "name": "calculate",
        "arguments": item.arguments,
    }
    item.model_dump = MagicMock(return_value=raw)
    reasoning = SimpleNamespace(
        type="reasoning",
        model_dump=MagicMock(
            return_value={
                "type": "reasoning",
                "encrypted_content": "opaque",
            }
        ),
    )
    response = SimpleNamespace(
        status="completed",
        output=[reasoning, item],
        output_text="",
        usage=SimpleNamespace(input_tokens=40, output_tokens=8),
    )
    client = SimpleNamespace(responses=SimpleNamespace(create=AsyncMock(return_value=response)))
    manager = MagicMock()
    manager.__aenter__ = AsyncMock(return_value=client)
    manager.__aexit__ = AsyncMock(return_value=None)
    with patch("memorybench.agent.providers.AsyncOpenAI", return_value=manager):
        history = [{"role": "user", "content": "test"}]
        turn = asyncio.run(OpenAIProvider(settings).respond(history, [{"type": "function"}]))
    assert turn.calls[0].name == "calculate"
    assert turn.continuation[0]["encrypted_content"] == "opaque"
    assert turn.usage == {"input_tokens": 40, "output_tokens": 8}
    kwargs = client.responses.create.call_args.kwargs
    assert kwargs["store"] is False
    assert kwargs["parallel_tool_calls"] is False
    assert kwargs["input"] == history


def test_real_sdk_round_trip_without_network(settings):
    import json

    import httpx
    from openai import AsyncOpenAI
    from pydantic import SecretStr

    from memorybench.agent.runner import AgentRunner
    from memorybench.tracing.store import RunStore

    settings.api_key = SecretStr("test-only-key")
    settings.provider = "openai"
    requests = []

    def handle(request):
        body = json.loads(request.content)
        requests.append(body)
        if len(requests) == 1:
            output = [
                {
                    "type": "function_call",
                    "id": "fc_1",
                    "call_id": "c1",
                    "name": "calculate",
                    "arguments": '{"expression":"2+2"}',
                    "status": "completed",
                }
            ]
        else:
            result = json.loads(body["input"][-1]["output"])
            assert result == {"ok": True, "result": {"value": 4}}
            output = [
                {
                    "type": "message",
                    "id": "msg_1",
                    "role": "assistant",
                    "status": "completed",
                    "content": [
                        {"type": "output_text", "text": "The answer is 4.", "annotations": []}
                    ],
                }
            ]
        return httpx.Response(
            200,
            json={
                "id": f"resp_{len(requests)}",
                "object": "response",
                "created_at": 1,
                "status": "completed",
                "model": settings.model,
                "output": output,
                "usage": {"input_tokens": 10, "output_tokens": 5, "total_tokens": 15},
            },
        )

    def factory(**kwargs):
        return AsyncOpenAI(
            **kwargs, http_client=httpx.AsyncClient(transport=httpx.MockTransport(handle))
        )

    with patch("memorybench.agent.providers.AsyncOpenAI", side_effect=factory):
        store = RunStore(settings.data_dir)
        runner = AgentRunner(settings, store, OpenAIProvider(settings))
        run = asyncio.run(runner.run("Calculate 2 + 2."))
    assert run["status"] == "completed"
    assert run["answer"] == "The answer is 4."
    assert len(requests) == 2
    assert requests[1]["input"][1]["type"] == "function_call"

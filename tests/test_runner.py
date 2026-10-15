import asyncio
import json

import pytest

from memorybench.agent.models import ModelTurn, ToolCall
from memorybench.agent.providers import DemoProvider
from memorybench.agent.runner import AgentRunner
from memorybench.samples import DEMO_TASK
from memorybench.tracing.store import RunStore


class ScriptedProvider:
    def __init__(self, turns):
        self.turns = iter(turns)
        self.histories = []

    async def respond(self, history, tools):
        self.histories.append(list(history))
        turn = next(self.turns)
        if isinstance(turn, Exception):
            raise turn
        return turn


def call(name="calculate", arguments='{"expression": "2+2"}', call_id="call_1"):
    return ModelTurn(
        calls=[ToolCall(call_id, name, arguments)],
        continuation=[
            {
                "type": "function_call",
                "call_id": call_id,
                "name": name,
                "arguments": arguments,
            }
        ],
    )


def execute(settings, provider, task="A task"):
    store = RunStore(settings.data_dir)
    return asyncio.run(AgentRunner(settings, store, provider).run(task))


def test_full_demo_writes_and_verifies(settings):
    run = execute(settings, DemoProvider(), DEMO_TASK)
    assert run["status"] == "completed"
    assert "$8.59" in run["answer"]
    artifact = settings.data_dir / "workspaces" / run["id"] / "experiment.txt"
    assert "$8.59" in artifact.read_text()
    assert sum(e["kind"] == "tool_call" for e in run["events"]) == 3
    assert run["events"][0]["kind"] == "run_started"
    assert run["events"][-1]["kind"] == "run_finished"
    assert all(e["duration_ms"] >= 0 for e in run["events"])


def test_tool_error_is_returned_to_model_for_recovery(settings):
    provider = ScriptedProvider([call(arguments="bad json"), ModelTurn(text="Recovered.")])
    run = execute(settings, provider)
    assert run["status"] == "completed"
    assert any(e["kind"] == "tool_error" for e in run["events"])
    output = json.loads(provider.histories[1][-1]["output"])
    assert output["ok"] is False


def test_model_error_is_durable(settings):
    run = execute(settings, ScriptedProvider([RuntimeError("provider unavailable")]))
    assert run["status"] == "failed"
    assert [e["kind"] for e in run["events"]][-3:] == [
        "model_error",
        "run_error",
        "run_finished",
    ]


def test_empty_model_response_fails(settings):
    assert execute(settings, ScriptedProvider([ModelTurn()]))["status"] == "failed"


def test_step_limit(settings):
    settings.max_steps = 1
    run = execute(settings, ScriptedProvider([call()]))
    assert run["status"] == "limited"


def test_tool_call_budget_prevents_extra_side_effects(settings):
    settings.max_tool_calls = 1
    turn = call()
    turn.calls.append(ToolCall("call_2", "write_file", '{"path":"x.txt","content":"x"}'))
    run = execute(settings, ScriptedProvider([turn]))
    assert run["status"] == "limited"
    assert not (settings.data_dir / "workspaces" / run["id"] / "x.txt").exists()


def test_duplicate_call_ids_fail(settings):
    run = execute(settings, ScriptedProvider([call(), call()]))
    assert run["status"] == "failed"
    assert sum(e["kind"] == "tool_call" for e in run["events"]) == 1


class SlowProvider:
    async def respond(self, history, tools):
        await asyncio.sleep(1)


def test_model_timeout(settings):
    settings.model_timeout_seconds = 0.01
    assert execute(settings, SlowProvider())["status"] == "limited"


def test_run_deadline(settings):
    settings.run_timeout_seconds = 0.01
    run = execute(settings, SlowProvider())
    assert run["status"] == "limited"
    assert any(e["kind"] == "model_error" for e in run["events"])


@pytest.mark.parametrize("task", ["", "   ", "a" * 8001])
def test_invalid_task_does_not_create_run(settings, task):
    with pytest.raises(ValueError):
        execute(settings, DemoProvider(), task)
    assert RunStore(settings.data_dir).recent() == []


def test_each_run_has_fresh_context_and_workspace(settings):
    first = execute(settings, DemoProvider(), DEMO_TASK)
    second = execute(settings, DemoProvider(), DEMO_TASK)
    assert first["id"] != second["id"]
    assert first["status"] == second["status"] == "completed"


def test_cancelled_run_is_recorded(settings):
    async def scenario():
        store = RunStore(settings.data_dir)
        runner = AgentRunner(settings, store, SlowProvider())
        task = asyncio.create_task(runner.run("task"))
        await asyncio.sleep(0.01)
        task.cancel()
        with pytest.raises(asyncio.CancelledError):
            await task
        return store.recent()[0]

    assert asyncio.run(scenario())["status"] == "cancelled"

"""Bounded task loop with durable events around every external operation."""

import asyncio
import json
from collections.abc import Callable
from time import perf_counter

from memorybench.agent.models import ModelProvider
from memorybench.config import Settings
from memorybench.tools.builtin import Workspace
from memorybench.tools.registry import ToolRegistry
from memorybench.tracing.store import RunStore, utc_now


class RunLimitError(RuntimeError):
    pass


class AgentRunner:
    def __init__(self, settings: Settings, store: RunStore, provider: ModelProvider):
        self.settings, self.store, self.provider = settings, store, provider

    async def run(self, task: str, on_event: Callable | None = None) -> dict:
        task = task.strip()
        if not task or len(task) > 8000:
            raise ValueError("Enter a task between 1 and 8,000 characters.")
        started = perf_counter()
        run = self.store.create(task, self.settings.public_config())

        def emit(kind: str, step: int = 0, duration_ms: float = 0, **data):
            event = self.store.append(run["id"], kind, step, duration_ms, **data)
            if on_event:
                on_event(event)

        try:
            emit("run_started", task=task, config=self.settings.public_config())
            workspace = Workspace(self.settings.data_dir / "workspaces" / run["id"])
            registry = ToolRegistry(workspace)
            # Future memory retrieval can enrich this fresh history. V0 uses only this task.
            history = [{"role": "user", "content": task}]
            async with asyncio.timeout(self.settings.run_timeout_seconds):
                run["answer"] = await self._loop(history, registry, emit)
            run["status"] = "completed"
        except asyncio.CancelledError:
            run["status"] = "cancelled"
            emit("run_error", error="Run cancelled.", error_type="CancelledError")
            raise
        except Exception as exc:
            run["status"] = (
                "limited" if isinstance(exc, (TimeoutError, RunLimitError)) else "failed"
            )
            emit(
                "run_error",
                error=str(exc) or "Run deadline reached.",
                error_type=type(exc).__name__,
            )
        finally:
            run["duration_ms"] = round((perf_counter() - started) * 1000, 3)
            run["finished_at"] = utc_now()
            # Future episodic writers can consume completed events after this commit.
            self.store.save(run)
            emit(
                "run_finished",
                duration_ms=run["duration_ms"],
                status=run["status"],
                answer=run["answer"],
            )
        return self.store.get(run["id"])

    async def _loop(self, history: list[dict], registry: ToolRegistry, emit: Callable) -> str:
        calls_used = 0
        seen_ids = set()
        for step in range(1, self.settings.max_steps + 1):
            emit(
                "model_request",
                step,
                model=self.settings.model,
                provider=self.settings.provider,
                history_items=len(history),
            )
            started = perf_counter()
            try:
                turn = await asyncio.wait_for(
                    self.provider.respond(history, registry.schemas()),
                    timeout=self.settings.model_timeout_seconds,
                )
            except BaseException as exc:
                emit(
                    "model_error",
                    step,
                    (perf_counter() - started) * 1000,
                    error=str(exc) or "Model call interrupted or timed out.",
                    error_type=type(exc).__name__,
                )
                raise
            emit(
                "model_response",
                step,
                (perf_counter() - started) * 1000,
                text=turn.text,
                usage=turn.usage,
                calls=[
                    {"call_id": call.call_id, "name": call.name, "arguments": call.arguments}
                    for call in turn.calls
                ],
            )
            if not turn.calls:
                if not turn.text.strip():
                    raise RuntimeError("The model returned no answer or tool calls.")
                return turn.text
            history.extend(turn.continuation)
            for call in turn.calls:
                if calls_used >= self.settings.max_tool_calls:
                    raise RunLimitError("Tool call limit reached. Try a smaller task.")
                if call.call_id in seen_ids:
                    raise RuntimeError("The model repeated a tool call ID.")
                seen_ids.add(call.call_id)
                calls_used += 1
                emit(
                    "tool_call",
                    step,
                    call_id=call.call_id,
                    name=call.name,
                    arguments=call.arguments,
                )
                started = perf_counter()
                try:
                    result = await registry.execute(
                        call.name, call.arguments, self.settings.tool_timeout_seconds
                    )
                    output = {"ok": True, "result": result}
                    kind = "tool_result"
                except BaseException as exc:
                    emit(
                        "tool_error",
                        step,
                        (perf_counter() - started) * 1000,
                        call_id=call.call_id,
                        name=call.name,
                        error=str(exc) or "Tool interrupted or timed out.",
                        error_type=type(exc).__name__,
                    )
                    if not isinstance(exc, Exception):
                        raise
                    output = {"ok": False, "error": str(exc) or "Tool timed out."}
                    kind = None
                if kind:
                    emit(
                        kind,
                        step,
                        (perf_counter() - started) * 1000,
                        call_id=call.call_id,
                        name=call.name,
                        result=result,
                    )
                history.append(
                    {
                        "type": "function_call_output",
                        "call_id": call.call_id,
                        "output": json.dumps(output),
                    }
                )
        raise RunLimitError("Model step limit reached. Try a smaller task or raise the limit.")

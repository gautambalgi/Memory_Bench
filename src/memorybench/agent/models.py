"""Small contracts that keep model SDK types outside the runner."""

from dataclasses import dataclass, field
from typing import Any, Protocol


@dataclass
class ToolCall:
    call_id: str
    name: str
    arguments: str


@dataclass
class ModelTurn:
    text: str = ""
    calls: list[ToolCall] = field(default_factory=list)
    # Preserve provider output items, including reasoning items, for the next request.
    continuation: list[dict[str, Any]] = field(default_factory=list)
    usage: dict[str, int] = field(default_factory=dict)


class ModelProvider(Protocol):
    async def respond(self, history: list[dict], tools: list[dict]) -> ModelTurn: ...

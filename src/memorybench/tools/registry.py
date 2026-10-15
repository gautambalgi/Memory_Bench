"""Tool discovery and input validation, independent of any model SDK."""

import asyncio
import json
from collections.abc import Callable
from dataclasses import dataclass

from jsonschema import Draft202012Validator

from memorybench.tools.builtin import Workspace, calculate, text_stats


@dataclass(frozen=True)
class Tool:
    name: str
    description: str
    properties: dict
    handler: Callable

    @property
    def schema(self) -> dict:
        return {
            "type": "object",
            "properties": self.properties,
            "required": list(self.properties),
            "additionalProperties": False,
        }


def string(limit: int) -> dict:
    return {"type": "string", "maxLength": limit}


class ToolRegistry:
    def __init__(self, workspace: Workspace):
        definitions = [
            Tool(
                "calculate",
                "Evaluate bounded arithmetic without executing code.",
                {"expression": string(500)},
                calculate,
            ),
            Tool(
                "write_file",
                "Create a new text file in this run's workspace. Never overwrites.",
                {"path": string(100), "content": string(16000)},
                workspace.write_file,
            ),
            Tool(
                "read_file",
                "Read a text file from this run's workspace.",
                {"path": string(100)},
                workspace.read_file,
            ),
            Tool(
                "list_files",
                "List up to 100 files in this run's workspace.",
                {},
                workspace.list_files,
            ),
            Tool(
                "text_stats",
                "Count characters, whitespace-separated words, and lines.",
                {"text": string(16000)},
                text_stats,
            ),
        ]
        self.tools = {tool.name: tool for tool in definitions}

    def schemas(self) -> list[dict]:
        return [
            {
                "type": "function",
                "name": tool.name,
                "description": tool.description,
                "parameters": tool.schema,
                "strict": True,
            }
            for tool in self.tools.values()
        ]

    async def execute(self, name: str, arguments: str, timeout: float) -> dict:
        if name not in self.tools:
            raise ValueError(f"Unknown tool: {name}")
        if len(arguments) > 100_000:
            raise ValueError("Tool arguments are too large.")
        tool = self.tools[name]
        parsed = json.loads(arguments)
        Draft202012Validator(tool.schema).validate(parsed)
        # Built-ins are bounded. Thread offloading keeps model/run deadlines responsive.
        # Future tools need their own I/O deadlines; cancelling a thread cannot stop its I/O.
        return await asyncio.wait_for(asyncio.to_thread(tool.handler, **parsed), timeout=timeout)

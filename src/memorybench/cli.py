"""Headless entry point for the same runner used by the dashboard."""

import argparse
import asyncio
import json

from memorybench.agent.providers import create_provider
from memorybench.agent.runner import AgentRunner
from memorybench.config import Settings
from memorybench.samples import DEMO_TASK
from memorybench.tracing.store import RunStore


def main():
    parser = argparse.ArgumentParser(description="Run a task with MemoryBench.")
    parser.add_argument("task", nargs="?", help="Task text. Required for live mode.")
    parser.add_argument("--provider", choices=["demo", "openai"])
    args = parser.parse_args()
    settings = Settings()
    if args.provider:
        settings = settings.model_copy(update={"provider": args.provider})
    task = args.task or (DEMO_TASK if settings.provider == "demo" else "")
    if not task:
        parser.error("Provide a task for live mode.")
    if settings.provider == "demo" and task != DEMO_TASK:
        parser.error("The guided demo runs only the built-in sample. Use --provider openai.")
    try:
        store = RunStore(settings.data_dir, (settings.api_key.get_secret_value(),))
        runner = AgentRunner(settings, store, create_provider(settings))
        run = asyncio.run(runner.run(task))
    except Exception as exc:
        detail = store.redactor.clean(str(exc)) if "store" in locals() else type(exc).__name__
        parser.exit(2, f"Could not start: {detail}\n")
    print(json.dumps(run, indent=2))
    if run["status"] != "completed":
        raise SystemExit(1)

"""Interactive run workbench. All user content uses escaped Streamlit components."""

import asyncio
import json
import sqlite3

import plotly.graph_objects as go
import streamlit as st
from pydantic import ValidationError

from memorybench.agent.providers import create_provider
from memorybench.agent.runner import AgentRunner
from memorybench.config import Settings
from memorybench.dashboard.style import CSS
from memorybench.samples import DEMO_TASK, SAMPLE_TASKS
from memorybench.tracing.store import RunStore


def inspect_run(run: dict):
    events = run["events"]
    st.markdown('<div class="eyebrow">02 / RUN OBSERVATORY</div>', unsafe_allow_html=True)
    st.subheader("Follow the work, step by step.")
    st.caption(f"Run {run['id'][:12]} | {run['started_at']} | {run['config']['provider']}")
    if run["status"] == "completed":
        st.success("Run completed. The full record is ready to explore.")
    elif run["status"] == "running":
        st.warning("This run has no recorded finish. It may still be active or was interrupted.")
    else:
        st.warning(f"Run {run['status']}. Open the error events below for details.")
    cols = st.columns(4)
    cols[0].metric("Wall time", f"{run['duration_ms'] / 1000:.2f} s")
    cols[1].metric("Model turns", sum(e["kind"] == "model_request" for e in events))
    cols[2].metric("Tool calls", sum(e["kind"] == "tool_call" for e in events))
    cols[3].metric("Errors", sum(e["kind"].endswith("error") for e in events))
    st.caption(
        "Completion means the agent returned an answer. Task correctness is not scored in V0."
    )
    answer_tab, timeline_tab, latency_tab, record_tab = st.tabs(
        ["Result", "Event timeline", "Where time went", "Run record"]
    )
    with answer_tab:
        with st.expander("Original task"):
            st.write(run["task"])
        if run["answer"]:
            st.markdown(run["answer"])
        else:
            st.info("No final answer was recorded. The timeline shows how far the agent got.")
        files = [
            e["data"]["result"]["path"]
            for e in events
            if e["kind"] == "tool_result" and e["data"]["name"] == "write_file"
        ]
        if files:
            st.caption("Files created in this run: " + ", ".join(files))
    with timeline_tab:
        left, right = st.columns([2, 1])
        search = left.text_input(
            "Find an event", placeholder="Tool name, result, or error", key=f"search_{run['id']}"
        )
        group = right.selectbox(
            "Show", ["All events", "Tools", "Model", "Errors"], key=f"filter_{run['id']}"
        )
        filtered = [
            event
            for event in events
            if (
                group == "All events"
                or (group == "Tools" and event["kind"].startswith("tool_"))
                or (group == "Model" and event["kind"].startswith("model_"))
                or (group == "Errors" and event["kind"].endswith("error"))
            )
            and search.lower() in json.dumps(event).lower()
        ]
        st.caption(
            f"{len(filtered)} of {len(events)} events. Select a row to inspect its contents."
        )
        if filtered:
            selected = st.select_slider(
                "Replay position",
                options=list(range(len(filtered))),
                value=len(filtered) - 1,
                key=f"replay_{run['id']}_{group}_{search}",
                format_func=lambda i: (
                    f"{filtered[i]['seq']:02d} / {filtered[i]['kind'].replace('_', ' ')}"
                ),
            )
            st.json(filtered[selected], expanded=True)
            for event in filtered:
                label = (
                    f"{event['seq']:02d}  |  {event['kind'].replace('_', ' ')}"
                    f"  |  step {event['step']}  |  {event['duration_ms']:.1f} ms"
                )
                with st.expander(label):
                    st.caption(event["at"])
                    st.json(event["data"])
        else:
            st.info("No events match this filter.")
    with latency_tab:
        measured = [
            e
            for e in events
            if e["kind"] in {"model_response", "model_error", "tool_result", "tool_error"}
        ]
        if measured:
            fig = go.Figure(
                go.Bar(
                    x=[e["duration_ms"] for e in measured],
                    y=[f"{e['seq']:02d}  {e['data'].get('name', 'model')}" for e in measured],
                    orientation="h",
                    marker_color=[
                        "#E4BF79"
                        if e["kind"].endswith("error")
                        else "#A6F4C5"
                        if e["kind"].startswith("tool")
                        else "#98BDFA"
                        for e in measured
                    ],
                    hovertemplate="%{y}<br>%{x:.2f} ms<extra></extra>",
                )
            )
            fig.update_layout(
                template="plotly_dark",
                paper_bgcolor="#101719",
                plot_bgcolor="#101719",
                font_color="#F2F6F3",
                xaxis_title="Operation time (ms)",
                yaxis={"autorange": "reversed"},
                margin={"l": 0, "r": 20, "t": 10, "b": 40},
                height=max(260, len(measured) * 42),
            )
            st.plotly_chart(fig, use_container_width=True)
            st.caption("Blue: model. Mint: tool. Amber: error. Hover for exact measurements.")
        else:
            st.info("No completed operations to chart yet.")
    with record_tab:
        st.write("A portable record of the task, configuration, and every recorded event.")
        st.download_button(
            "Download run JSON",
            json.dumps(run, indent=2),
            file_name=f"memorybench-{run['id'][:12]}.json",
            mime="application/json",
        )
        st.json(run["config"])


def main():
    st.set_page_config(page_title="MemoryBench | Agent workbench", page_icon="◈", layout="wide")
    st.markdown(CSS, unsafe_allow_html=True)
    try:
        settings = Settings()
    except ValidationError:
        st.error("Some settings are invalid. Check .env against the ranges in .env.example.")
        st.stop()
    try:
        store = RunStore(settings.data_dir, (settings.api_key.get_secret_value(),))
    except (OSError, sqlite3.Error):
        st.error("The data directory is not writable. Check MB_DATA_DIR and folder permissions.")
        st.stop()
    with st.sidebar:
        st.markdown('<div class="lab-mark">MB / 00</div>', unsafe_allow_html=True)
        st.title("MemoryBench")
        st.caption("An open notebook for agent behavior.")
        st.divider()
        st.markdown("**Your workbench**")
        mode = st.radio(
            "Execution mode",
            ["Guided demo", "Live AI"],
            index=0 if settings.provider == "demo" else 1,
        )
        if mode == "Guided demo":
            st.caption("A scripted sample with real tool execution. No API key needed.")
        else:
            st.caption(f"Model: {settings.model}. Credentials are read from your environment.")
        steps = st.slider("Model step limit", 1, 50, settings.max_steps)
        st.caption(f"Run deadline: {settings.run_timeout_seconds:g} seconds")
        st.divider()
        st.markdown("**Recent runs**")
        recent = store.recent()
        options = ["New run"] + [r["id"] for r in recent]
        labels = {r["id"]: f"{r['status']} / {r['task'][:38]}" for r in recent}
        active = st.session_state.get("active_run", "New run")
        chosen = st.selectbox(
            "Open a run",
            options,
            index=options.index(active) if active in options else 0,
            format_func=lambda value: labels.get(value, value),
        )
        st.caption("Saved locally. Each run starts with a fresh context.")
        st.divider()
        st.caption("VERSION 0 / OBSERVE FIRST")
        st.caption("Memory, benchmarks, and evaluation will build on this execution record.")
    st.markdown(
        '<div class="eyebrow">MEMORYBENCH / AGENT RESEARCH WORKBENCH</div>', unsafe_allow_html=True
    )
    st.title("Make every step visible.")
    st.markdown(
        '<div class="hero-copy">Give an agent a task. Watch it use its tools. '
        "Keep a clear record of what happened, where it struggled, and how long it took."
        "</div>",
        unsafe_allow_html=True,
    )
    if chosen != "New run":
        inspect_run(store.get(chosen))
        return
    st.markdown('<div class="eyebrow">01 / SET UP AN EXPERIMENT</div>', unsafe_allow_html=True)
    editor, context = st.columns([2.2, 1], gap="large")
    demo = mode == "Guided demo"
    with editor:
        sample = st.selectbox("Start with a sample", list(SAMPLE_TASKS), disabled=demo)
        task = st.text_area(
            "What should the agent do?",
            value=DEMO_TASK if demo else SAMPLE_TASKS[sample],
            height=145,
            max_chars=8000,
            disabled=demo,
            key=f"task_{mode}_{sample}",
        )
        if demo:
            st.caption("This fixed sample calculates a cost, saves a file, and reads it back.")
        ready = demo or bool(settings.api_key.get_secret_value().strip())
        if not ready:
            st.info("Add OPENAI_API_KEY to .env, then refresh to enable Live AI.")
        start = st.button(
            "Run experiment",
            type="primary",
            disabled=not ready or not task.strip(),
            use_container_width=True,
        )
    with context:
        st.markdown("### A small, useful toolkit")
        st.write("Calculate numbers. Count words. Create, read, and list files.")
        st.markdown(
            '<div class="note">Every run starts fresh. The record persists. '
            "Advanced memory comes later.</div>",
            unsafe_allow_html=True,
        )
        st.caption(
            "Files stay in a separate folder for each run. Existing files are never overwritten."
        )
    if start:
        run_settings = settings.model_copy(
            update={"provider": "demo" if demo else "openai", "max_steps": steps}
        )
        with st.status("Starting your experiment...", expanded=True) as status:

            def update(event):
                name = event["data"].get("name", "")
                st.write(f"{event['seq']:02d} / {event['kind'].replace('_', ' ')} {name}")

            try:
                runner = AgentRunner(run_settings, store, create_provider(run_settings))
                run = asyncio.run(runner.run(task, update))
            except Exception:
                status.update(label="Could not start the run.", state="error")
                st.error("Check your settings and local data folder, then try again.")
                return
            status.update(
                label=f"Run {run['status']}",
                expanded=False,
                state="complete" if run["status"] == "completed" else "error",
            )
        st.session_state["active_run"] = run["id"]
        st.rerun()
    st.divider()
    st.caption("Observe now. Understand over time. MemoryBench V0.")

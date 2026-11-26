"""Read and display the recorded Study Assistant experiment."""

import json
from pathlib import Path
from statistics import median

import streamlit as st

from memorybench.dashboard.text import display_text

MODES = {
    "Session only": "baseline",
    "Saved summary": "saved-summary",
    "Retrieved notes": "retrieved-notes",
}
RECALL_CASES = {"fresh-chat-recall", "updated-fact"}
NOTES_FINDINGS = {
    "same-chat-topic": "Gave a beginner exercise using a loop over a list.",
    "hints-first": "Gave a conceptual hint without revealing the solution.",
    "latest-preference": "Provided and explained the full loop when asked.",
    "fresh-chat-recall": "Recalled nested for loops from the selected learner's note.",
    "updated-fact": "Recalled June 19, 2030 after that date replaced June 12.",
    "irrelevant-detail": "Answered in two sentences without mentioning the saved study group.",
    "learner-isolation": "Leo received no notes. Maya correctly received her topic and nickname.",
}


def read_json(path: Path) -> dict:
    return display_text(json.loads(path.read_text(encoding="utf-8")))


def load_comparison(root: Path) -> tuple[list[dict], dict, dict]:
    scenarios = read_json(root / "scenarios/study-assistant-v1.json")["cases"]
    reports = root / "reports"
    records = {
        mode: {
            case["id"]: case
            for case in read_json(reports / f"Study-Assistant-{slug}-v1-evidence.json")["cases"]
        }
        for mode, slug in MODES.items()
    }
    retry = read_json(reports / "Study-Assistant-retrieved-notes-v1-retest.json")
    expected = {case["id"] for case in scenarios}
    if any(set(cases) != expected for cases in records.values()) or retry["id"] not in expected:
        raise ValueError("Saved files do not cover the same scenarios.")
    return scenarios, records, retry


def verdict(mode: str, attempt: dict, retry_id: str) -> str:
    if mode != "Retrieved notes":
        return attempt["verdict"]
    return "BLOCKED" if attempt["id"] == retry_id and attempt.get("attempt", 1) == 1 else "PASS"


def metrics(attempts: list[dict]) -> dict:
    turns = [turn for attempt in attempts for turn in attempt["turns"]]
    calls = [call for turn in turns for call in turn["calls"]]
    usage = [call.get("usage", call) for call in calls]
    inputs = sum(row["input_tokens"] for row in usage)
    outputs = sum(row["output_tokens"] for row in usage)
    cached = sum(row.get("cached_input_tokens") or 0 for row in usage)
    # Historical standard rates used in all three reports for GPT-5 nano.
    cost = ((inputs - cached) * 0.05 + cached * 0.005 + outputs * 0.40) / 1_000_000
    return {
        "calls": len(calls),
        "input": inputs,
        "output": outputs,
        "median": median(turn["wall_seconds"] for turn in turns),
        "cost": cost,
    }


def show_turn(mode: str, turn: dict, *, expand_memory: bool = False) -> None:
    st.caption(f"{turn['learner'].title()} · Chat {turn['chat']}")
    if "reply" in turn:
        st.markdown(turn["reply"])
    if "error" in turn:
        st.error(turn["error"])
    with st.expander("Memory supplied to the tutor", expanded=expand_memory):
        call = next((call for call in turn["calls"] if call.get("purpose") != "note_update"), {})
        if mode == "Session only":
            st.caption("This request used the current chat's messages.")
        elif mode == "Saved summary":
            st.text(call.get("summary_supplied") or "No saved summary was supplied.")
        else:
            notes = call.get("notes_supplied", {})
            if notes:
                for topic, fact in notes.items():
                    st.text(f"{topic.replace('_', ' ').title()}: {fact}")
            else:
                st.caption("No matching notes were supplied.")
    st.caption(f"{turn['wall_seconds']:.2f} s · {len(turn['calls'])} model calls")


def render_scenario_explorer() -> None:
    st.title("Try a memory scenario")
    st.caption("Explore recorded tutor replies. Switching scenarios or modes makes no API calls.")
    try:
        scenarios, records, retry = load_comparison(Path.cwd())
    except (OSError, ValueError, KeyError, TypeError):
        st.error("Could not load the recorded scenarios.")
        return

    by_id = {case["id"]: case for case in scenarios}
    case_id = st.selectbox(
        "Scenario",
        list(by_id),
        index=list(by_id).index("updated-fact"),
        format_func=lambda key: by_id[key]["title"],
        key="explorer_scenario",
    )
    mode = st.radio("Memory mode", list(MODES), horizontal=True, key="explorer_mode")
    case = by_id[case_id]
    with st.expander("Read the scenario messages"):
        for i, turn in enumerate(case["turns"], 1):
            st.caption(f"Message {i} · {turn['learner'].title()} · Chat {turn['chat']}")
            st.write(turn["message"])
    scored_turns = [check["turn"] for check in case["checks"]]
    turn_number = st.selectbox(
        "Learner message",
        range(1, len(case["turns"]) + 1),
        index=scored_turns[-1] - 1,
        format_func=lambda i: f"Message {i}" + (" · Scored" if i in scored_turns else ""),
        key=f"explorer_turn_{case_id}",
    )
    attempt = records[mode][case_id]
    if mode == "Retrieved notes" and case_id == retry["id"]:
        attempt_label = st.radio("Recorded attempt", ["Completed retry", "First attempt"])
        if attempt_label == "Completed retry":
            attempt = retry

    st.subheader("Learner message")
    st.write(case["turns"][turn_number - 1]["message"])
    st.subheader("Recorded tutor reply")
    show_turn(mode, attempt["turns"][turn_number - 1], expand_memory=True)
    outcome = verdict(mode, attempt, retry["id"])
    st.subheader(f"Scenario result · {outcome.title()}")
    if outcome == "BLOCKED":
        st.write("The first setup reply was incomplete, so no practice topic was saved.")
    elif turn_number not in scored_turns:
        st.caption("This message sets up the scenario. Choose a scored message to see the finding.")
    elif mode == "Retrieved notes":
        if case_id == "learner-isolation" and turn_number == 2:
            st.write("Leo received no notes or details from Maya's profile.")
        else:
            st.write(NOTES_FINDINGS[case_id])
    else:
        check = next(row for row in attempt["checkpoints"] if row["turn"] == turn_number)
        st.write(check["reason"])


def render_comparison() -> None:
    st.title("Compare memory modes")
    st.caption("Seven Study Assistant scenarios, using saved results from GPT-5 nano.")
    try:
        scenarios, records, retry = load_comparison(Path.cwd())
    except (OSError, ValueError, KeyError, TypeError):
        st.error("Could not load the comparison. Check the saved files in reports and scenarios.")
        return

    retry_id = retry["id"]
    include_retry = st.toggle("Use the completed retry in the comparison", value=True)
    selected_records = {mode: cases.copy() for mode, cases in records.items()}
    if include_retry:
        selected_records["Retrieved notes"][retry_id] = retry

    cards = st.columns(3)
    for card, (mode, cases) in zip(cards, selected_records.items(), strict=True):
        with card:
            st.subheader(mode)
            passed = sum(verdict(mode, attempt, retry_id) == "PASS" for attempt in cases.values())
            recall = sum(
                case.get("cross_chat_recall") == "correct"
                or (mode == "Retrieved notes" and verdict(mode, case, retry_id) == "PASS")
                for key, case in cases.items()
                if key in RECALL_CASES
            )
            st.metric("Scenarios passed", f"{passed}/{len(scenarios)}")
            st.metric("Correct recall across chats", f"{recall}/{len(RECALL_CASES)}")

    totals = [
        {"Measure": name}
        for name in (
            "Median wait per message",
            "Model calls",
            "Input tokens",
            "Output tokens",
            "Estimated cost",
        )
    ]
    for mode, cases in selected_records.items():
        m = metrics(list(cases.values()))
        values = (
            f"{m['median']:.2f} s",
            str(m["calls"]),
            f"{m['input']:,}",
            f"{m['output']:,}",
            f"${m['cost']:.6f}",
        )
        for row, value in zip(totals, values, strict=True):
            row[mode] = value
    st.table(totals)
    st.caption(
        "Costs use the historical rates from the reports and include memory update calls. "
        "With the retry selected, metrics use one completed attempt per scenario."
    )

    st.subheader("Inspect a scenario")
    by_id = {case["id"]: case for case in scenarios}
    scenario_id = st.selectbox("Scenario", by_id, format_func=lambda key: by_id[key]["title"])
    scenario = by_id[scenario_id]
    turns = sorted(check["turn"] for check in scenario["checks"])
    turn_number = st.selectbox(
        "Learner message",
        range(1, len(scenario["turns"]) + 1),
        index=turns[-1] - 1,
        format_func=lambda index: f"Message {index}" + (" · Scored" if index in turns else ""),
        key=f"compare_turn_{scenario_id}",
    )
    st.markdown("**Question or message**")
    st.write(scenario["turns"][turn_number - 1]["message"])
    if scenario_id == retry_id:
        st.info(
            "Retrieved notes was blocked on its first attempt. The model returned an incomplete "
            "setup reply, so no note was saved. The fresh retry recalled the topic."
        )
    for column, (mode, cases) in zip(st.columns(3), selected_records.items(), strict=True):
        with column:
            attempt = cases[scenario_id]
            outcome = verdict(mode, attempt, retry_id)
            st.subheader(mode)
            st.markdown(f"**Scenario verdict · {outcome}**")
            check = next(
                (row for row in attempt.get("checkpoints", []) if row["turn"] == turn_number), None
            )
            if check:
                st.caption(check["reason"])
            elif mode == "Retrieved notes" and turn_number in turns:
                if outcome == "PASS" and scenario_id == "learner-isolation":
                    st.caption(
                        "Leo received no notes and learned none of Maya's details."
                        if turn_number == 2
                        else "Maya received her own topic and nickname."
                    )
                elif outcome == "PASS":
                    st.caption(NOTES_FINDINGS[scenario_id])
                else:
                    st.caption("The setup reply was incomplete. Recall could not be scored fairly.")
            show_turn(mode, attempt["turns"][turn_number - 1])

import json
from pathlib import Path
from unittest.mock import AsyncMock

from streamlit.testing.v1 import AppTest

from memorybench.agent.models import ModelTurn
from memorybench.dashboard import study
from memorybench.memory.summaries import SummaryStore

APP = Path(__file__).resolve().parents[1] / "app.py"


def test_retry_and_new_chat_keep_request_history_correct(monkeypatch):
    monkeypatch.setenv("OPENAI_API_KEY", "test-only")
    respond = AsyncMock(
        side_effect=[
            ModelTurn(text="Let's practice loops."),
            TimeoutError(),
            ModelTurn(text="Try printing each item in a list."),
            ModelTurn(text="What topic are you studying?"),
        ]
    )
    monkeypatch.setattr(study.OpenAIProvider, "respond", respond)

    app = AppTest.from_file(str(APP)).run(timeout=20)
    next(radio for radio in app.radio if radio.label == "Views").set_value("Study Assistant").run()
    app.chat_input[0].set_value("I struggle with loops.").run()
    app.chat_input[0].set_value("Give me an exercise.").run()
    assert "timed out" in app.error[0].value
    assert len(app.chat_message) == 3
    next(button for button in app.button if button.label == "Retry reply").click().run()
    assert len(app.chat_message) == 4
    expected = [
        {"role": "user", "content": "I struggle with loops."},
        {"role": "assistant", "content": "Let's practice loops."},
        {"role": "user", "content": "Give me an exercise."},
    ]
    assert respond.await_args_list[1].args == (expected, [])
    assert respond.await_args_list[2].args == (expected, [])
    next(button for button in app.button if button.label == "New chat").click().run()
    assert not app.chat_message
    app.chat_input[0].set_value("What topic was I struggling with?").run()
    assert respond.await_args.args == (
        [{"role": "user", "content": "What topic was I struggling with?"}],
        [],
    )


def test_summary_survives_new_session_and_keeps_learners_separate(tmp_path, monkeypatch):
    monkeypatch.setenv("OPENAI_API_KEY", "test-only")
    monkeypatch.setenv("MB_DATA_DIR", str(tmp_path))
    respond = AsyncMock(
        side_effect=[
            ModelTurn(text="Got it."),
            ModelTurn(text="Struggles with nested loops."),
            ModelTurn(text="What are you studying?"),
            ModelTurn(text="NO_FACTS"),
            ModelTurn(text="Nested loops."),
            ModelTurn(text="Struggles with nested loops."),
        ]
    )
    monkeypatch.setattr(study.OpenAIProvider, "respond", respond)
    store = SummaryStore(tmp_path)
    maya = store.create("Maya")
    leo = store.create("Leo")

    def open_profile(learner_id):
        app = AppTest.from_file(str(APP)).run(timeout=20)
        next(r for r in app.radio if r.label == "Views").set_value("Study Assistant").run()
        app.radio(key="study_mode_picker").set_value(study.SAVED_SUMMARY).run()
        app.selectbox(key="study_profile_picker").set_value(learner_id).run()
        assert not app.exception and not app.chat_message
        return app

    first = open_profile(maya)
    first.chat_input[0].set_value("I struggle with nested loops.").run()
    assert not first.exception and not first.warning
    assert store.get(maya).text == "Struggles with nested loops."
    for profile in (leo, maya):
        app = open_profile(profile)
        app.chat_input[0].set_value("What am I studying?").run()
        assert not app.exception and not app.warning
    assert store.get(leo).text == ""
    assert json.loads(respond.await_args_list[2].args[0][0]["content"]) == {
        "saved_learner_summary": ""
    }
    assert json.loads(respond.await_args_list[4].args[0][0]["content"]) == {
        "saved_learner_summary": "Struggles with nested loops."
    }


def test_summary_store_rejects_stale_revision(tmp_path):
    store = SummaryStore(tmp_path)
    learner = store.get(store.create("Maya"))
    assert store.update(learner, "Current exam is June 19.")
    assert not store.update(learner, "Old exam is June 12.")
    assert store.get(learner.id).text == "Current exam is June 19."


def test_failed_summary_update_keeps_the_reply_and_existing_summary(tmp_path, monkeypatch):
    monkeypatch.setenv("OPENAI_API_KEY", "test-only")
    monkeypatch.setenv("MB_DATA_DIR", str(tmp_path))
    store = SummaryStore(tmp_path)
    learner = store.get(store.create("Maya"))
    assert store.update(learner, "Practices for loops.")
    respond = AsyncMock(side_effect=[ModelTurn(text="Thanks for the update."), TimeoutError()])
    monkeypatch.setattr(study.OpenAIProvider, "respond", respond)

    app = AppTest.from_file(str(APP)).run(timeout=20)
    next(r for r in app.radio if r.label == "Views").set_value("Study Assistant").run()
    app.radio(key="study_mode_picker").set_value(study.SAVED_SUMMARY).run()
    app.selectbox(key="study_profile_picker").set_value(learner.id).run()
    app.chat_input[0].set_value("I am now studying tuples.").run()
    assert not app.exception and not app.error
    assert "could not update" in app.warning[0].value
    assert app.chat_message[-1].markdown[0].value == "Thanks for the update."
    assert store.get(learner.id).text == "Practices for loops."
    assert respond.await_count == 2

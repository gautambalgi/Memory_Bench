from pathlib import Path

from streamlit.testing.v1 import AppTest

from memorybench.tracing.store import RunStore

APP = Path(__file__).resolve().parents[1] / "app.py"


def test_dashboard_demo_and_run_inspector(tmp_path, monkeypatch):
    monkeypatch.setenv("MB_DATA_DIR", str(tmp_path))
    monkeypatch.setenv("MB_PROVIDER", "demo")
    monkeypatch.setenv("OPENAI_API_KEY", "")
    app = AppTest.from_file(str(APP)).run(timeout=20)
    assert not app.exception
    assert "Make every step visible." in [title.value for title in app.title]
    next(button for button in app.button if button.label == "Run experiment").click().run(
        timeout=20
    )
    assert not app.exception
    assert any("Run completed" in message.value for message in app.success)
    assert len(app.metric) == 4
    assert any("$8.59" in item.value for item in app.markdown)
    # Filter to errors, then restore the timeline and inspect an earlier event.
    filters = next(item for item in app.selectbox if item.label == "Show")
    filters.select("Errors").run()
    assert not app.exception
    assert any("No events match" in item.value for item in app.info)
    next(item for item in app.selectbox if item.label == "Show").select("All events").run()
    app.select_slider[0].set_value(0).run()
    assert not app.exception


def test_live_mode_explains_missing_credentials(tmp_path, monkeypatch):
    monkeypatch.setenv("MB_DATA_DIR", str(tmp_path))
    monkeypatch.setenv("MB_PROVIDER", "openai")
    monkeypatch.setenv("OPENAI_API_KEY", "")
    app = AppTest.from_file(str(APP)).run(timeout=20)
    assert not app.exception
    assert next(button for button in app.button if button.label == "Run experiment").disabled
    assert any("API key in the sidebar" in message.value for message in app.info)


def test_sidebar_key_overrides_local_key_and_clears(monkeypatch, tmp_path):
    from memorybench.dashboard import app as dashboard

    monkeypatch.setenv("OPENAI_API_KEY", "fake-local-key")
    monkeypatch.setenv("MB_DATA_DIR", str(tmp_path))
    active_keys = []
    monkeypatch.setattr(
        dashboard,
        "render_run_dashboard",
        lambda settings: active_keys.append(settings.api_key.get_secret_value()),
    )
    app = AppTest.from_file(str(APP)).run()
    next(field for field in app.text_input if field.label == "OpenAI API key").set_value(
        "fake-session-key"
    )
    next(
        button for button in app.button if button.label == "Use key for this session"
    ).click().run()
    assert active_keys[-1] == "fake-session-key"
    other_session = AppTest.from_file(str(APP)).run()
    assert not other_session.exception and active_keys[-1] == "fake-local-key"
    next(button for button in app.button if button.label == "Clear session key").click().run()
    assert active_keys[-1] == "fake-local-key"


def test_repeated_tasks_open_the_selected_run(tmp_path, monkeypatch):
    monkeypatch.setenv("MB_DATA_DIR", str(tmp_path))
    store = RunStore(tmp_path)
    first = store.create("Same task", {"provider": "demo"})
    second = store.create("Same task", {"provider": "demo"})

    app = AppTest.from_file(str(APP)).run(timeout=20)
    picker = next(widget for widget in app.selectbox if widget.label == "Open a run")
    assert len(set(picker.options)) == 3
    for run in (first, second):
        picker = next(widget for widget in app.selectbox if widget.label == "Open a run")
        picker.select(run["id"]).run()
        assert not app.exception
        assert any(run["id"][:12] in caption.value for caption in app.caption)


def test_invalid_settings_show_a_readable_message(monkeypatch):
    monkeypatch.setenv("MB_MAX_STEPS", "0")
    app = AppTest.from_file(str(APP)).run(timeout=20)
    assert not app.exception
    assert any("settings are invalid" in message.value for message in app.error)

from pathlib import Path

from streamlit.testing.v1 import AppTest

APP = Path(__file__).resolve().parents[1] / "app.py"


def test_dashboard_demo_and_run_inspector(tmp_path, monkeypatch):
    monkeypatch.setenv("MB_DATA_DIR", str(tmp_path))
    monkeypatch.setenv("MB_PROVIDER", "demo")
    monkeypatch.setenv("OPENAI_API_KEY", "")
    app = AppTest.from_file(str(APP)).run(timeout=20)
    assert not app.exception
    assert "Make every step visible." in [title.value for title in app.title]
    app.button[0].click().run(timeout=20)
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
    assert app.button[0].disabled
    assert any("OPENAI_API_KEY" in message.value for message in app.info)


def test_invalid_settings_show_a_readable_message(monkeypatch):
    monkeypatch.setenv("MB_MAX_STEPS", "0")
    app = AppTest.from_file(str(APP)).run(timeout=20)
    assert not app.exception
    assert any("settings are invalid" in message.value for message in app.error)

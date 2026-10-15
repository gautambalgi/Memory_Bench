import pytest
from pydantic import ValidationError

from memorybench.config import Settings


def test_environment_overrides_dotenv(tmp_path, monkeypatch):
    env = tmp_path / ".env"
    env.write_text("MB_MAX_STEPS=4\nMB_MODEL=example-model\n")
    monkeypatch.setenv("MB_MAX_STEPS", "7")
    settings = Settings(_env_file=env)
    assert settings.max_steps == 7
    assert settings.model == "example-model"


@pytest.mark.parametrize(
    "values",
    [
        {"max_steps": 0},
        {"provider": "unsupported"},
        {"model": " "},
        {"tool_timeout_seconds": -1},
        {"max_tool_calls": 101},
    ],
)
def test_bad_configuration_is_rejected(values):
    with pytest.raises(ValidationError):
        Settings(_env_file=None, **values)


def test_public_config_does_not_contain_key():
    settings = Settings(_env_file=None, api_key="private-key")
    assert "private-key" not in str(settings.public_config())

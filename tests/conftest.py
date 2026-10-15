import pytest

from memorybench.config import Settings


@pytest.fixture
def settings(tmp_path):
    return Settings(_env_file=None, provider="demo", data_dir=tmp_path, api_key="", max_steps=8)

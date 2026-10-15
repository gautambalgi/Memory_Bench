"""Validated environment settings. Secrets never enter run metadata."""

from pathlib import Path
from typing import Literal

from pydantic import Field, SecretStr, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_prefix="MB_", env_file=".env", extra="ignore", populate_by_name=True
    )
    provider: Literal["demo", "openai"] = "demo"
    api_key: SecretStr = Field(default=SecretStr(""), validation_alias="OPENAI_API_KEY")
    model: str = "gpt-4.1-mini"
    max_steps: int = Field(default=12, ge=1, le=50)
    max_tool_calls: int = Field(default=24, ge=1, le=100)
    model_timeout_seconds: float = Field(default=60, gt=0, le=300)
    tool_timeout_seconds: float = Field(default=10, gt=0, le=60)
    run_timeout_seconds: float = Field(default=180, gt=0, le=900)
    max_output_tokens: int = Field(default=2000, ge=128, le=16000)
    data_dir: Path = Path("data")

    @field_validator("model")
    @classmethod
    def model_not_blank(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("Choose a model name.")
        return value.strip()

    def public_config(self) -> dict:
        return self.model_dump(mode="json", exclude={"api_key"})

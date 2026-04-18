from __future__ import annotations

from pathlib import Path
import tomllib

from pydantic import BaseModel, Field, ValidationError


class CollectorConfig(BaseModel):
    greenhouse_boards: list[str] = Field(default_factory=list)
    seed_urls: list[str] = Field(default_factory=list)
    html_fallback_urls: list[str] = Field(default_factory=list)


class AppConfig(BaseModel):
    database_path: str = "data/jobs.sqlite3"
    request_timeout_seconds: float = 20.0
    user_agent: str = "job-finder/0.1"
    tls_verify: bool = True
    tls_ca_bundle: str | None = None
    collectors: CollectorConfig = Field(default_factory=CollectorConfig)

    @property
    def http_verify(self) -> bool | str:
        if self.tls_ca_bundle and self.tls_ca_bundle.strip():
            return self.tls_ca_bundle.strip()
        return self.tls_verify


def load_config(path: Path) -> AppConfig:
    if not path.exists():
        raise FileNotFoundError(f"Config file not found: {path}")

    with path.open("rb") as fh:
        raw = tomllib.load(fh)

    try:
        return AppConfig.model_validate(raw)
    except ValidationError as exc:
        raise ValueError(f"Invalid config file: {path}\n{exc}") from exc


def render_default_config() -> str:
    return """database_path = "data/jobs.sqlite3"
request_timeout_seconds = 20.0
user_agent = "job-finder/0.1"
tls_verify = true
# tls_ca_bundle = "/path/to/corporate-ca.pem"

[collectors]
greenhouse_boards = [
    "anthropic",
    "deepmind",
    "waymo",
]
seed_urls = [
    "https://boards.greenhouse.io/anthropic",
    "https://boards.greenhouse.io/deepmind",
    "https://boards.greenhouse.io/waymo",
]
html_fallback_urls = []
"""

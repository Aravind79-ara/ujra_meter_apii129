from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

PROJECT_ROOT = Path(__file__).resolve().parents[3]


class Settings(BaseSettings):
    urja_base_url: str = "https://urja-ops.flockenergy.tech"
    urja_username: str = ""
    urja_password: str = ""
    api_host: str = "0.0.0.0"
    api_port: int = 8000
    frontend_url: str = "http://localhost:3000"
    log_level: str = "INFO"
    request_timeout: float = 15.0
    demo_mode: bool = False

    model_config = SettingsConfigDict(env_file=PROJECT_ROOT / ".env", case_sensitive=False, extra="ignore")


@lru_cache
def get_settings() -> Settings:
    return Settings()


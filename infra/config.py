"""
Configuração de runtime (infra/), lida de variáveis de ambiente / .env.

Fica em infra/ porque é detalhe de implantação — os use cases não
conhecem nem dependem destas configurações.
"""

from __future__ import annotations

from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    database_url: str = "sqlite:///./photus.db"
    jwt_secret: str = "change-me"
    jwt_expire_minutes: int = 60


@lru_cache
def get_settings() -> Settings:
    return Settings()

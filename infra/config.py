
from __future__ import annotations

from functools import lru_cache
from pathlib import Path
from typing import Literal

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    database_url: str = "sqlite:///./photus.db"
    jwt_secret: str = "change-me"
    jwt_expire_minutes: int = 60

    photus_b_base_url: str = "http://localhost:8001"
    photus_b_timeout_seconds: float = 15.0
    uploads_dir: str = "uploads"

    # UC06 — onde roda o pipeline de visão computacional:
    #   "local" -> subprocess dos binários C++ dos repos irmãos (dev na máquina, sem Docker);
    #   "http"  -> serviço `photus-engine` em outro container (docker-compose).
    pipeline_backend: Literal["local", "http"] = "local"
    photus_engine_base_url: str = "http://localhost:8002"
    # Cobre a espera na fila do engine (um lote por vez) + o processamento.
    photus_engine_timeout_seconds: float = 600.0

    # UC06 modo "local" — binários C++ dos repos irmãos.
    preprocessor_root: str = "../ai-pre-process-images"
    photus_a_root: str = "../photus-a"
    # O pré-processador só aceita imagens sob uma allowlist hardcoded
    # (`<...>/photus-system/data/uploads/`); vazio => deriva do repo irmão photus-system.
    pipeline_staging_dir: str = ""
    pipeline_timeout_seconds: float = 300.0

    @property
    def resolved_pipeline_staging_dir(self) -> str:
        if self.pipeline_staging_dir:
            return self.pipeline_staging_dir
        sibling = Path(self.preprocessor_root).resolve().parent
        return str(sibling / "photus-system" / "data" / "uploads")


@lru_cache
def get_settings() -> Settings:
    return Settings()

"""Application settings loaded from environment variables."""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()


@dataclass(frozen=True)
class Settings:
    """Runtime settings for the advertising optimization pipeline."""

    artifact_dir: Path = field(
        default_factory=lambda: Path(
            os.getenv(
                "PIPELINE_ARTIFACT_DIR",
                "/tmp/optimal_advertising_pressure",
            ),
        ),
    )
    db_host: str = field(default_factory=lambda: os.getenv("DB_HOST", "localhost"))
    db_port: int = field(default_factory=lambda: int(os.getenv("DB_PORT", "5432")))
    db_name: str = field(default_factory=lambda: os.getenv("DB_NAME", "airflow"))
    db_user: str = field(default_factory=lambda: os.getenv("DB_USER", "airflow"))
    db_password: str = field(
        default_factory=lambda: os.getenv("DB_PASSWORD", "airflow"),
        repr=False,
    )
    db_url: str | None = field(
        default_factory=lambda: os.getenv("DATABASE_URL"),
        repr=False,
    )

    @property
    def database_url(self) -> str:
        """Return an explicit database URL or build one from DB settings."""
        if self.db_url:
            return self.db_url
        return (
            f"postgresql+psycopg2://{self.db_user}:{self.db_password}"
            f"@{self.db_host}:{self.db_port}/{self.db_name}"
        )

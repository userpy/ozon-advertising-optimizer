from pathlib import Path

from services.settings import Settings


def test_settings_reads_artifact_dir_from_environment(monkeypatch) -> None:
    monkeypatch.setenv("PIPELINE_ARTIFACT_DIR", "/tmp/custom-artifacts")

    settings = Settings()

    assert settings.artifact_dir == Path("/tmp/custom-artifacts")


def test_settings_builds_database_url_from_environment(monkeypatch) -> None:
    monkeypatch.delenv("DATABASE_URL", raising=False)
    monkeypatch.setenv("DB_HOST", "database")
    monkeypatch.setenv("DB_PORT", "5433")
    monkeypatch.setenv("DB_NAME", "optimizer")
    monkeypatch.setenv("DB_USER", "optimizer_user")
    monkeypatch.setenv("DB_PASSWORD", "secret")

    settings = Settings()

    assert settings.database_url == (
        "postgresql+psycopg2://optimizer_user:secret@database:5433/optimizer"
    )


def test_settings_prefers_explicit_database_url(monkeypatch) -> None:
    database_url = "postgresql+psycopg2://user:password@host:5432/database"
    monkeypatch.setenv("DATABASE_URL", database_url)

    settings = Settings()

    assert settings.database_url == database_url

from pathlib import Path

from app.core.config import Settings


def test_cors_origins_accepts_single_and_comma_separated_env_values(tmp_path: Path) -> None:
    env_file = tmp_path / ".env"
    env_file.write_text(
        "CORS_ORIGINS=http://localhost:3000,http://localhost:5173\n", encoding="utf-8"
    )

    settings = Settings(_env_file=env_file)

    assert settings.cors_origins == ["http://localhost:3000", "http://localhost:5173"]


def test_cors_origins_preserves_json_array_configuration(tmp_path: Path) -> None:
    env_file = tmp_path / ".env"
    env_file.write_text(
        'CORS_ORIGINS=["http://localhost:3000", "http://localhost:5173"]\n',
        encoding="utf-8",
    )

    settings = Settings(_env_file=env_file)

    assert settings.cors_origins == ["http://localhost:3000", "http://localhost:5173"]

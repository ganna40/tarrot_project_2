from pathlib import Path

from app.database import normalize_database_url


def test_render_postgres_url_uses_psycopg3_driver():
    assert (
        normalize_database_url("postgresql://user:pass@db.internal:5432/tarot")
        == "postgresql+psycopg://user:pass@db.internal:5432/tarot"
    )


def test_explicit_sqlalchemy_driver_url_is_unchanged():
    url = "postgresql+psycopg://user:pass@db.internal:5432/tarot"
    assert normalize_database_url(url) == url


def test_render_blueprint_provisions_web_and_postgres():
    root = Path(__file__).resolve().parents[2]
    blueprint = root / "render.yaml"
    text = blueprint.read_text(encoding="utf-8")

    for expected in (
        "name: tarot-engine-api-ganna40",
        "type: web",
        "runtime: docker",
        "plan: free",
        "region: singapore",
        "branch: new",
        "dockerContext: ./backend",
        "dockerfilePath: ./backend/Dockerfile",
        "healthCheckPath: /health",
        "autoDeployTrigger: checksPass",
        "key: DATABASE_URL",
        "fromDatabase:",
        "property: connectionString",
        "key: ALLOWED_ORIGINS",
        "https://ganna40.github.io",
        "name: tarot-engine-db-ganna40",
    ):
        assert expected in text

    dockerfile = (root / "backend" / "Dockerfile").read_text(encoding="utf-8")
    assert "${PORT:-8000}" in dockerfile

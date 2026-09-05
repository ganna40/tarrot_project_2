from pathlib import Path

from ingestion import build_public_domain_dataset as builder


DATA_DIR = Path(__file__).resolve().parents[1] / "data" / "curated"
CSV_FILES = (
    "sources.csv",
    "interpretation_tags.csv",
    "card_meanings.csv",
    "card_meaning_tags.csv",
    "card_correspondences.csv",
    "relation_rules.csv",
)


def test_committed_curated_package_is_deterministically_generated(tmp_path, monkeypatch):
    monkeypatch.setattr(builder, "OUT", tmp_path)
    builder.build()

    for filename in CSV_FILES:
        assert (tmp_path / filename).read_bytes() == (DATA_DIR / filename).read_bytes(), filename


def test_source_register_and_curated_readme_are_present():
    root = Path(__file__).resolve().parents[2]
    assert (root / "docs" / "data" / "public-domain-source-register.md").is_file()
    readme = (DATA_DIR / "README.md").read_text(encoding="utf-8")
    assert "156" in readme
    assert "DESIGNED" in readme

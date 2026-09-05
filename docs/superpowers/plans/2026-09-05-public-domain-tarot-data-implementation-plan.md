# Public-Domain Tarot Data Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Replace the 10-card demo seed with a source-traceable 78-card RWS knowledge set containing 156 meanings, Golden Dawn correspondences, controlled tags, and reusable relation rules.

**Architecture:** Curated CSV files are the review surface. A standard-library validator checks source rights, coverage, foreign keys, ranges, and historical edge cases. The FastAPI startup seed loads only validated records into the existing normalized PostgreSQL tables; the rule engine remains deterministic and OpenAI remains a language-only layer.

**Tech Stack:** Python 3.12, csv, SQLAlchemy 2, FastAPI, PostgreSQL 16, pytest, GitHub Actions.

**Spec:** `docs/superpowers/specs/2026-09-05-tarot-engine-v1-design.md`

## Global Constraints

- Core knowledge tables must not use JSON/JSONB.
- Exactly 78 RWS card identities and 156 GENERAL meanings are required.
- Meaning source: A. E. Waite, *The Pictorial Key to the Tarot*, Part III.
- Golden Dawn source: Book T material published as Liber LXXVIII in *The Equinox* I(8), 1912.
- Historical source wording must be paraphrased into Korean; long source passages are not copied.
- All production rows must retain source code, source locator, derivation status, and review status.
- Relation rules are editorial abstractions and must be marked `DESIGNED`, not falsely attributed to a historical author.
- OpenAI does not decide verdict, score, or flow.

---

### Task 1: Define the curated-data contract and failing coverage tests

**Files:**
- Create: `backend/tests/test_curated_dataset.py`
- Create: `backend/tests/test_public_domain_seed.py`

**Interfaces:**
- Produces: `load_curated_dataset() -> CuratedDataset`
- Produces: `validate_curated_dataset(dataset) -> ValidationReport`
- Produces: `seed_public_domain_knowledge(session: Session) -> None`

- [ ] Write tests requiring 78 identities, 156 meanings, exactly one primary tag per meaning, full element coverage, 36 decan cards, 22 Major Hebrew-letter/path records, four Aces at Kether, sixteen court-element records, and at least 30 relation rules.
- [ ] Run `python -m pytest backend/tests/test_curated_dataset.py backend/tests/test_public_domain_seed.py -q` and confirm failure because the data module does not exist.

### Task 2: Build the public-domain candidate CSV package

**Files:**
- Create: `ingestion/build_public_domain_dataset.py`
- Create: `backend/data/curated/sources.csv`
- Create: `backend/data/curated/interpretation_tags.csv`
- Create: `backend/data/curated/card_meanings.csv`
- Create: `backend/data/curated/card_meaning_tags.csv`
- Create: `backend/data/curated/card_correspondences.csv`
- Create: `backend/data/curated/relation_rules.csv`
- Create: `backend/data/curated/README.md`

**Interfaces:**
- CSV keys use existing engine card codes such as `TEN_OF_SWORDS`.
- Meaning uniqueness key: `(card_code, source_code, orientation, context)`.
- Correspondence uniqueness key: `(card_code, source_code, type, value)`.

- [ ] Encode all 78 source-derived upright/reversed Korean paraphrases and controlled tags.
- [ ] Generate Golden Dawn Major, Ace, court, Sephirah, planet, zodiac, decan, and title correspondences.
- [ ] Generate editorial tag-transition rules with `origin=DESIGNED` and no historical source claim.
- [ ] Run the generator twice and verify byte-identical output.

### Task 3: Add deterministic validation and loading

**Files:**
- Create: `backend/app/curated_data.py`
- Create: `ingestion/validate_candidates.py`
- Create: `ingestion/load_candidates.py`
- Modify: `backend/app/seed.py`

**Interfaces:**
- `load_curated_dataset(base_path: Path | None = None) -> CuratedDataset`
- `validate_curated_dataset(dataset: CuratedDataset) -> ValidationReport`
- `seed_public_domain_knowledge(session: Session) -> None`

- [ ] Implement CSV parsing with explicit typed records and no pandas dependency.
- [ ] Reject missing cards, orientations, tags, source rights, invalid ranges, duplicate keys, and correspondence coverage gaps.
- [ ] Load records idempotently and use `APPROVED` only for the reviewed curated package.
- [ ] Run the new unit tests until green.

### Task 4: Switch application startup to the public-domain seed

**Files:**
- Modify: `backend/app/main.py`
- Modify: `backend/app/config.py`
- Modify: `backend/tests/test_api.py`
- Modify: `backend/tests/test_repository.py`

**Interfaces:**
- Startup defaults to `seed_public_domain_knowledge`.
- `seed_demo_knowledge` remains only for legacy fixture compatibility.

- [ ] Add an API test proving a formerly unsupported card such as `FOOL` now resolves.
- [ ] Add a repository test proving every card has approved upright and reversed GENERAL meanings.
- [ ] Implement the startup change and make all tests pass.

### Task 5: Align elemental dignity logic with Book T and expand traceability

**Files:**
- Modify: `backend/app/repository.py`
- Modify: `backend/tests/test_engine.py`
- Modify: `backend/tests/test_repository.py`

**Interfaces:**
- Friendly pairs: Fire–Air, Fire–Earth, Air–Water.
- Hostile pairs: Fire–Water, Air–Earth.
- Same element strengthens; unstated pairs remain neutral.

- [ ] Write failing tests for friendly, hostile, same, and neutral pairs.
- [ ] Implement bounded modifiers without changing verdict after OpenAI.
- [ ] Confirm trace includes historical source codes and locators.

### Task 6: Integrate data verification into CI and documentation

**Files:**
- Modify: `.github/workflows/ci.yml`
- Modify: `README.md`
- Create: `docs/data/public-domain-source-register.md`
- Create: `backend/tests/test_data_files.py`

**Interfaces:**
- CI command: `PYTHONPATH=backend python ingestion/validate_candidates.py`.
- PostgreSQL CI asserts 78 cards and 156 approved GENERAL meanings.

- [ ] Add deterministic dataset validation before backend tests.
- [ ] Extend PostgreSQL smoke validation to assert meanings, tags, correspondences, and rules.
- [ ] Document exact sources, public-domain basis, normalization decisions, Two of Cups reversal exception, and court-card mapping.

### Task 7: Full verification and GitHub integration

**Files:** all changed files.

- [ ] Run `python -m pytest -q`.
- [ ] Run `PYTHONPATH=backend python ingestion/validate_candidates.py`.
- [ ] Run `npm test && npm run check:static`.
- [ ] Commit to the `new` branch through the GitHub API.
- [ ] Confirm the resulting GitHub Actions run completes successfully, including the PostgreSQL service check.

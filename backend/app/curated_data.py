from __future__ import annotations

import csv
from collections import Counter, defaultdict
from dataclasses import dataclass, field
from pathlib import Path
from typing import TypeVar


DEFAULT_CURATED_DATA_PATH = Path(__file__).resolve().parents[1] / "data" / "curated"


@dataclass(frozen=True)
class SourceRecord:
    code: str
    title: str
    author: str
    publication_year: int | None
    source_type: str
    license_status: str
    source_url: str
    rights_basis: str
    priority: int
    is_active: bool


@dataclass(frozen=True)
class TagRecord:
    code: str
    name_ko: str
    description: str


@dataclass(frozen=True)
class MeaningRecord:
    card_code: str
    source_code: str
    orientation: str
    context: str
    meaning_text: str
    advice_text: str | None
    warning_text: str | None
    polarity: float
    action_level: float
    speed_level: float
    stability_level: float
    ending_level: float
    origin: str
    source_locator: str
    page_start: int | None
    page_end: int | None
    priority: int
    review_status: str
    review_method: str
    review_notes: str
    is_active: bool


@dataclass(frozen=True)
class MeaningTagRecord:
    card_code: str
    orientation: str
    context: str
    tag_code: str
    weight: float
    is_primary: bool


@dataclass(frozen=True)
class CorrespondenceRecord:
    card_code: str
    source_code: str
    correspondence_type: str
    value: str
    source_locator: str
    page_start: int | None
    page_end: int | None
    priority: int
    review_status: str
    review_method: str
    review_notes: str
    is_active: bool


@dataclass(frozen=True)
class RelationRuleRecord:
    from_tag_code: str
    to_tag_code: str
    context: str
    relation_type: str
    transition_text: str
    score_delta: float
    priority: int
    source_code: str
    source_locator: str
    origin: str
    review_status: str
    review_method: str
    review_notes: str
    is_active: bool


@dataclass(frozen=True)
class CuratedDataset:
    sources: tuple[SourceRecord, ...]
    tags: tuple[TagRecord, ...]
    meanings: tuple[MeaningRecord, ...]
    meaning_tags: tuple[MeaningTagRecord, ...]
    correspondences: tuple[CorrespondenceRecord, ...]
    relation_rules: tuple[RelationRuleRecord, ...]
    base_path: Path


@dataclass
class ValidationReport:
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    metrics: dict[str, int] = field(default_factory=dict)

    @property
    def is_valid(self) -> bool:
        return not self.errors

    def raise_for_errors(self) -> None:
        if self.errors:
            raise ValueError("Curated tarot dataset validation failed:\n- " + "\n- ".join(self.errors))


T = TypeVar("T")


def _read_rows(path: Path) -> list[dict[str, str]]:
    if not path.is_file():
        raise FileNotFoundError(f"Curated data file not found: {path}")
    with path.open("r", encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def _required(row: dict[str, str], key: str, filename: str) -> str:
    value = (row.get(key) or "").strip()
    if not value:
        raise ValueError(f"{filename}: required column {key!r} is empty")
    return value


def _optional(row: dict[str, str], key: str) -> str | None:
    value = (row.get(key) or "").strip()
    return value or None


def _bool(row: dict[str, str], key: str, filename: str) -> bool:
    value = _required(row, key, filename).lower()
    if value not in {"true", "false"}:
        raise ValueError(f"{filename}: {key} must be true or false, got {value!r}")
    return value == "true"


def _int(row: dict[str, str], key: str, filename: str, *, optional: bool = False) -> int | None:
    raw = (row.get(key) or "").strip()
    if optional and not raw:
        return None
    if not raw:
        raise ValueError(f"{filename}: required integer {key!r} is empty")
    try:
        return int(raw)
    except ValueError as exc:
        raise ValueError(f"{filename}: {key} must be an integer, got {raw!r}") from exc


def _float(row: dict[str, str], key: str, filename: str) -> float:
    raw = _required(row, key, filename)
    try:
        return float(raw)
    except ValueError as exc:
        raise ValueError(f"{filename}: {key} must be numeric, got {raw!r}") from exc


def load_curated_dataset(base_path: Path | str | None = None) -> CuratedDataset:
    base = Path(base_path) if base_path is not None else DEFAULT_CURATED_DATA_PATH

    source_file = "sources.csv"
    sources = tuple(
        SourceRecord(
            code=_required(row, "code", source_file),
            title=_required(row, "title", source_file),
            author=(row.get("author") or "").strip(),
            publication_year=_int(row, "publication_year", source_file, optional=True),
            source_type=_required(row, "source_type", source_file),
            license_status=_required(row, "license_status", source_file),
            source_url=_required(row, "source_url", source_file),
            rights_basis=_required(row, "rights_basis", source_file),
            priority=int(_int(row, "priority", source_file) or 0),
            is_active=_bool(row, "is_active", source_file),
        )
        for row in _read_rows(base / source_file)
    )

    tag_file = "interpretation_tags.csv"
    tags = tuple(
        TagRecord(
            code=_required(row, "code", tag_file),
            name_ko=_required(row, "name_ko", tag_file),
            description=_required(row, "description", tag_file),
        )
        for row in _read_rows(base / tag_file)
    )

    meaning_file = "card_meanings.csv"
    meanings = tuple(
        MeaningRecord(
            card_code=_required(row, "card_code", meaning_file),
            source_code=_required(row, "source_code", meaning_file),
            orientation=_required(row, "orientation", meaning_file),
            context=_required(row, "context", meaning_file),
            meaning_text=_required(row, "meaning_text", meaning_file),
            advice_text=_optional(row, "advice_text"),
            warning_text=_optional(row, "warning_text"),
            polarity=_float(row, "polarity", meaning_file),
            action_level=_float(row, "action_level", meaning_file),
            speed_level=_float(row, "speed_level", meaning_file),
            stability_level=_float(row, "stability_level", meaning_file),
            ending_level=_float(row, "ending_level", meaning_file),
            origin=_required(row, "origin", meaning_file),
            source_locator=_required(row, "source_locator", meaning_file),
            page_start=_int(row, "page_start", meaning_file, optional=True),
            page_end=_int(row, "page_end", meaning_file, optional=True),
            priority=int(_int(row, "priority", meaning_file) or 0),
            review_status=_required(row, "review_status", meaning_file),
            review_method=_required(row, "review_method", meaning_file),
            review_notes=_required(row, "review_notes", meaning_file),
            is_active=_bool(row, "is_active", meaning_file),
        )
        for row in _read_rows(base / meaning_file)
    )

    link_file = "card_meaning_tags.csv"
    meaning_tags = tuple(
        MeaningTagRecord(
            card_code=_required(row, "card_code", link_file),
            orientation=_required(row, "orientation", link_file),
            context=_required(row, "context", link_file),
            tag_code=_required(row, "tag_code", link_file),
            weight=_float(row, "weight", link_file),
            is_primary=_bool(row, "is_primary", link_file),
        )
        for row in _read_rows(base / link_file)
    )

    corr_file = "card_correspondences.csv"
    correspondences = tuple(
        CorrespondenceRecord(
            card_code=_required(row, "card_code", corr_file),
            source_code=_required(row, "source_code", corr_file),
            correspondence_type=_required(row, "correspondence_type", corr_file),
            value=_required(row, "value", corr_file),
            source_locator=_required(row, "source_locator", corr_file),
            page_start=_int(row, "page_start", corr_file, optional=True),
            page_end=_int(row, "page_end", corr_file, optional=True),
            priority=int(_int(row, "priority", corr_file) or 0),
            review_status=_required(row, "review_status", corr_file),
            review_method=_required(row, "review_method", corr_file),
            review_notes=_required(row, "review_notes", corr_file),
            is_active=_bool(row, "is_active", corr_file),
        )
        for row in _read_rows(base / corr_file)
    )

    rule_file = "relation_rules.csv"
    relation_rules = tuple(
        RelationRuleRecord(
            from_tag_code=_required(row, "from_tag_code", rule_file),
            to_tag_code=_required(row, "to_tag_code", rule_file),
            context=(row.get("context") or "").strip(),
            relation_type=_required(row, "relation_type", rule_file),
            transition_text=_required(row, "transition_text", rule_file),
            score_delta=_float(row, "score_delta", rule_file),
            priority=int(_int(row, "priority", rule_file) or 0),
            source_code=(row.get("source_code") or "").strip(),
            source_locator=_required(row, "source_locator", rule_file),
            origin=_required(row, "origin", rule_file),
            review_status=_required(row, "review_status", rule_file),
            review_method=_required(row, "review_method", rule_file),
            review_notes=_required(row, "review_notes", rule_file),
            is_active=_bool(row, "is_active", rule_file),
        )
        for row in _read_rows(base / rule_file)
    )

    return CuratedDataset(
        sources=sources,
        tags=tags,
        meanings=meanings,
        meaning_tags=meaning_tags,
        correspondences=correspondences,
        relation_rules=relation_rules,
        base_path=base,
    )


def _duplicates(values: list[tuple[object, ...]]) -> list[tuple[object, ...]]:
    return [key for key, count in Counter(values).items() if count > 1]


def validate_curated_dataset(dataset: CuratedDataset) -> ValidationReport:
    # Imported lazily so seed.py can import this module inside its loader without a cycle.
    from app.seed import all_card_rows

    report = ValidationReport()
    cards = all_card_rows()
    card_by_code = {card.code: card for card in cards}
    expected_cards = set(card_by_code)

    report.metrics.update(
        sources=len(dataset.sources),
        tags=len(dataset.tags),
        meanings=len(dataset.meanings),
        meaning_tags=len(dataset.meaning_tags),
        correspondences=len(dataset.correspondences),
        relation_rules=len(dataset.relation_rules),
    )

    if len(cards) != 78 or len(expected_cards) != 78:
        report.errors.append(f"Engine card catalogue must contain 78 unique cards; got {len(expected_cards)}")

    source_codes = [row.code for row in dataset.sources]
    duplicate_sources = _duplicates([(code,) for code in source_codes])
    if duplicate_sources:
        report.errors.append(f"Duplicate source codes: {duplicate_sources}")
    source_by_code = {row.code: row for row in dataset.sources}
    for code in ("WAITE_PKD_1910", "GOLDEN_DAWN_BOOK_T_1912"):
        source = source_by_code.get(code)
        if source is None:
            report.errors.append(f"Missing required public-domain source: {code}")
            continue
        if source.license_status != "PUBLIC_DOMAIN":
            report.errors.append(f"{code} must be marked PUBLIC_DOMAIN")
        if not source.source_url.startswith("https://"):
            report.errors.append(f"{code} must use an HTTPS source URL")
        if not source.rights_basis:
            report.errors.append(f"{code} is missing a rights basis")
        if not source.is_active:
            report.errors.append(f"{code} must be active")

    tag_codes = [row.code for row in dataset.tags]
    duplicate_tags = _duplicates([(code,) for code in tag_codes])
    if duplicate_tags:
        report.errors.append(f"Duplicate tag codes: {duplicate_tags}")
    tag_code_set = set(tag_codes)

    meaning_keys = [(row.card_code, row.source_code, row.orientation, row.context) for row in dataset.meanings]
    duplicate_meanings = _duplicates(meaning_keys)
    if duplicate_meanings:
        report.errors.append(f"Duplicate meaning records: {duplicate_meanings[:5]}")

    expected_meanings = {
        (code, "WAITE_PKD_1910", orientation, "GENERAL")
        for code in expected_cards
        for orientation in ("UPRIGHT", "REVERSED")
    }
    actual_meanings = set(meaning_keys)
    if actual_meanings != expected_meanings:
        missing = sorted(expected_meanings - actual_meanings)
        extra = sorted(actual_meanings - expected_meanings)
        report.errors.append(f"Meaning coverage mismatch: missing={missing[:5]}, extra={extra[:5]}")
    if len(dataset.meanings) != 156:
        report.errors.append(f"Expected 156 meanings, got {len(dataset.meanings)}")

    for row in dataset.meanings:
        if row.card_code not in expected_cards:
            report.errors.append(f"Unknown card in meanings: {row.card_code}")
        if row.source_code not in source_by_code:
            report.errors.append(f"Unknown source in meanings: {row.source_code}")
        if row.orientation not in {"UPRIGHT", "REVERSED"}:
            report.errors.append(f"Invalid orientation for {row.card_code}: {row.orientation}")
        if row.context != "GENERAL":
            report.errors.append(f"v1 curated meanings must use GENERAL context: {row.card_code}/{row.context}")
        if row.origin not in {"SOURCE", "DERIVED", "EDITORIAL"}:
            report.errors.append(f"Invalid meaning origin for {row.card_code}: {row.origin}")
        if row.review_status != "APPROVED" or not row.is_active:
            report.errors.append(f"Meaning is not approved and active: {row.card_code}/{row.orientation}")
        if not row.source_locator or not row.review_method or not row.review_notes:
            report.errors.append(f"Meaning lacks traceability: {row.card_code}/{row.orientation}")
        if not -5 <= row.polarity <= 5:
            report.errors.append(f"Polarity out of range: {row.card_code}/{row.orientation}")
        for label, value in (
            ("action", row.action_level),
            ("speed", row.speed_level),
            ("stability", row.stability_level),
            ("ending", row.ending_level),
        ):
            if not 0 <= value <= 5:
                report.errors.append(f"{label} out of range: {row.card_code}/{row.orientation}")

    short_meaning_keys = {(row.card_code, row.orientation, row.context) for row in dataset.meanings}
    link_keys: defaultdict[tuple[str, str, str], list[MeaningTagRecord]] = defaultdict(list)
    duplicate_links = _duplicates(
        [(row.card_code, row.orientation, row.context, row.tag_code) for row in dataset.meaning_tags]
    )
    if duplicate_links:
        report.errors.append(f"Duplicate meaning-tag links: {duplicate_links[:5]}")
    for row in dataset.meaning_tags:
        key = (row.card_code, row.orientation, row.context)
        link_keys[key].append(row)
        if key not in short_meaning_keys:
            report.errors.append(f"Meaning-tag link has no meaning: {key}")
        if row.tag_code not in tag_code_set:
            report.errors.append(f"Unknown tag in meaning link: {row.tag_code}")
        if not 0 < row.weight <= 1:
            report.errors.append(f"Meaning-tag weight out of range: {key}/{row.tag_code}")
    if set(link_keys) != short_meaning_keys:
        missing_links = sorted(short_meaning_keys - set(link_keys))
        report.errors.append(f"Meanings without tag links: {missing_links[:5]}")
    for key, rows in link_keys.items():
        if sum(1 for row in rows if row.is_primary) != 1:
            report.errors.append(f"Meaning must have exactly one primary tag: {key}")

    correspondence_keys = [
        (row.card_code, row.source_code, row.correspondence_type, row.value)
        for row in dataset.correspondences
    ]
    duplicate_correspondences = _duplicates(correspondence_keys)
    if duplicate_correspondences:
        report.errors.append(f"Duplicate correspondences: {duplicate_correspondences[:5]}")

    by_card: defaultdict[str, defaultdict[str, set[str]]] = defaultdict(lambda: defaultdict(set))
    for row in dataset.correspondences:
        if row.card_code not in expected_cards:
            report.errors.append(f"Unknown card in correspondence: {row.card_code}")
        if row.source_code not in source_by_code:
            report.errors.append(f"Unknown source in correspondence: {row.source_code}")
        if row.review_status != "APPROVED" or not row.is_active:
            report.errors.append(f"Correspondence is not approved and active: {row.card_code}/{row.correspondence_type}")
        if not row.source_locator or not row.review_method or not row.review_notes:
            report.errors.append(f"Correspondence lacks traceability: {row.card_code}/{row.correspondence_type}")
        by_card[row.card_code][row.correspondence_type].add(row.value)

    for card in cards:
        for kind in ("ELEMENT", "GD_TITLE"):
            if not by_card[card.code][kind]:
                report.errors.append(f"Missing {kind} correspondence: {card.code}")

    majors = [card for card in cards if card.arcana == "MAJOR"]
    for card in majors:
        for kind in ("HEBREW_LETTER", "TREE_PATH"):
            if not by_card[card.code][kind]:
                report.errors.append(f"Missing Major {kind}: {card.code}")

    pips = [
        card
        for card in cards
        if card.arcana == "MINOR" and card.rank not in {"ACE", "PAGE", "KNIGHT", "QUEEN", "KING"}
    ]
    if len(pips) != 36:
        report.errors.append(f"Expected 36 numbered pips, got {len(pips)}")
    for card in pips:
        for kind in ("PLANET", "ZODIAC", "DECAN", "SEPHIRAH", "GD_TITLE"):
            if not by_card[card.code][kind]:
                report.errors.append(f"Missing pip {kind}: {card.code}")

    aces = [card for card in cards if card.rank == "ACE"]
    for card in aces:
        if by_card[card.code]["SEPHIRAH"] != {"KETHER"}:
            report.errors.append(f"Ace must map to KETHER: {card.code}")

    courts = [card for card in cards if card.rank in {"PAGE", "KNIGHT", "QUEEN", "KING"}]
    for card in courts:
        if not by_card[card.code]["COURT_ELEMENT"]:
            report.errors.append(f"Missing court element: {card.code}")

    rule_keys = [
        (row.from_tag_code, row.to_tag_code, row.context, row.relation_type)
        for row in dataset.relation_rules
    ]
    duplicate_rules = _duplicates(rule_keys)
    if duplicate_rules:
        report.errors.append(f"Duplicate relation rules: {duplicate_rules[:5]}")
    if len(dataset.relation_rules) < 30:
        report.errors.append(f"Expected at least 30 relation rules, got {len(dataset.relation_rules)}")
    for row in dataset.relation_rules:
        if row.from_tag_code not in tag_code_set or row.to_tag_code not in tag_code_set:
            report.errors.append(f"Relation rule references unknown tag: {row.from_tag_code}->{row.to_tag_code}")
        if row.source_code:
            report.errors.append(
                f"Designed relation rule must not claim a historical source: {row.from_tag_code}->{row.to_tag_code}"
            )
        if row.origin != "DESIGNED":
            report.errors.append(f"Relation rule must use DESIGNED origin: {row.from_tag_code}->{row.to_tag_code}")
        if row.review_status != "APPROVED" or not row.is_active:
            report.errors.append(f"Relation rule is not approved and active: {row.from_tag_code}->{row.to_tag_code}")
        if not -2 <= row.score_delta <= 2:
            report.errors.append(f"Relation score out of range: {row.from_tag_code}->{row.to_tag_code}")
        if not row.source_locator or not row.review_method or not row.review_notes:
            report.errors.append(f"Relation rule lacks editorial trace: {row.from_tag_code}->{row.to_tag_code}")

    if len(dataset.tags) > 120:
        report.warnings.append(
            f"The controlled vocabulary has {len(dataset.tags)} tags; consider consolidating after evaluation."
        )

    return report

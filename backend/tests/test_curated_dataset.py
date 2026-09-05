from collections import Counter, defaultdict

from app.curated_data import load_curated_dataset, validate_curated_dataset
from app.seed import all_card_rows


def test_curated_dataset_has_complete_78_card_meaning_coverage():
    dataset = load_curated_dataset()
    report = validate_curated_dataset(dataset)

    assert report.errors == []
    assert len({card.code for card in all_card_rows()}) == 78
    assert len(dataset.meanings) == 156

    coverage = Counter((row.card_code, row.orientation, row.context) for row in dataset.meanings)
    expected = {
        (card.code, orientation, "GENERAL")
        for card in all_card_rows()
        for orientation in ("UPRIGHT", "REVERSED")
    }
    assert set(coverage) == expected
    assert all(count == 1 for count in coverage.values())


def test_every_meaning_has_exactly_one_primary_tag():
    dataset = load_curated_dataset()
    links = defaultdict(list)
    for link in dataset.meaning_tags:
        links[(link.card_code, link.orientation, link.context)].append(link)

    assert len(links) == 156
    for key, rows in links.items():
        assert rows, key
        assert sum(row.is_primary for row in rows) == 1, key
        assert all(0 < row.weight <= 1 for row in rows), key


def test_golden_dawn_correspondence_coverage_is_complete():
    dataset = load_curated_dataset()
    by_card = defaultdict(lambda: defaultdict(set))
    for row in dataset.correspondences:
        by_card[row.card_code][row.correspondence_type].add(row.value)

    cards = all_card_rows()
    assert all(by_card[card.code]["ELEMENT"] for card in cards)
    assert all(by_card[card.code]["GD_TITLE"] for card in cards)

    numbered_pips = [
        card for card in cards
        if card.arcana == "MINOR" and card.rank not in {"ACE", "PAGE", "KNIGHT", "QUEEN", "KING"}
    ]
    assert len(numbered_pips) == 36
    for card in numbered_pips:
        for kind in ("PLANET", "ZODIAC", "DECAN", "SEPHIRAH", "GD_TITLE"):
            assert by_card[card.code][kind], (card.code, kind)

    majors = [card for card in cards if card.arcana == "MAJOR"]
    assert len(majors) == 22
    for card in majors:
        assert by_card[card.code]["HEBREW_LETTER"], card.code
        assert by_card[card.code]["TREE_PATH"], card.code

    aces = [card for card in cards if card.rank == "ACE"]
    assert len(aces) == 4
    assert all(by_card[card.code]["SEPHIRAH"] == {"KETHER"} for card in aces)

    courts = [card for card in cards if card.rank in {"PAGE", "KNIGHT", "QUEEN", "KING"}]
    assert len(courts) == 16
    assert all(by_card[card.code]["COURT_ELEMENT"] for card in courts)


def test_sources_are_public_domain_and_rules_are_not_false_source_claims():
    dataset = load_curated_dataset()

    source_by_code = {source.code: source for source in dataset.sources}
    assert source_by_code["WAITE_PKD_1910"].license_status == "PUBLIC_DOMAIN"
    assert source_by_code["GOLDEN_DAWN_BOOK_T_1912"].license_status == "PUBLIC_DOMAIN"
    assert source_by_code["WAITE_PKD_1910"].source_url.startswith("https://")
    assert source_by_code["GOLDEN_DAWN_BOOK_T_1912"].source_url.startswith("https://")

    assert len(dataset.relation_rules) >= 30
    assert all(rule.origin == "DESIGNED" for rule in dataset.relation_rules)
    assert all(rule.source_code == "" for rule in dataset.relation_rules)


def test_historical_normalization_exceptions_are_explicit_and_traceable():
    dataset = load_curated_dataset()

    two_cups_reversed = next(
        row
        for row in dataset.meanings
        if row.card_code == "TWO_OF_CUPS" and row.orientation == "REVERSED"
    )
    assert "Part III §4" in two_cups_reversed.source_locator

    cards = {card.code: card for card in all_card_rows()}
    assert cards["STRENGTH"].number == 8
    assert cards["JUSTICE"].number == 11

    by_key = {
        (row.card_code, row.correspondence_type): row.value
        for row in dataset.correspondences
    }
    assert by_key[("KNIGHT_OF_WANDS", "COURT_ELEMENT")] == "FIRE_OF_FIRE"
    assert by_key[("QUEEN_OF_CUPS", "COURT_ELEMENT")] == "WATER_OF_WATER"
    assert by_key[("KING_OF_SWORDS", "COURT_ELEMENT")] == "AIR_OF_AIR"
    assert by_key[("PAGE_OF_PENTACLES", "COURT_ELEMENT")] == "EARTH_OF_EARTH"

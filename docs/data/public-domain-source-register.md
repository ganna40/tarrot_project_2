# Public-Domain Tarot Source Register

## Dataset release

- Dataset: `CURATED_TAROT_V1`
- Cards: 78 RWS identities
- Meanings: 156 (`UPRIGHT` + `REVERSED`, `GENERAL` context)
- Meaning-tag links: 342
- Golden Dawn correspondences: 385
- Relation rules: 55
- Runtime storage: normalized PostgreSQL tables; no JSON/JSONB in core knowledge

`APPROVED` means the row passed this project's source, structure, and editorial checks. It does not mean endorsement by an academic institution or a professional diviner.

## WAITE_PKD_1910

| Field | Value |
|---|---|
| Work | *The Pictorial Key to the Tarot*, Part III |
| Author | Arthur Edward Waite |
| First publication | 1910 |
| Role | Upright and reversed divinatory meanings for all 78 cards |
| Primary access | <https://en.wikisource.org/wiki/The_Pictorial_Key_to_the_Tarot/Part_3> |
| Scan and rights record | <https://commons.wikimedia.org/wiki/File:The_Pictorial_Key_to_the_Tarot.pdf> |
| Dataset transformation | Short Korean editorial paraphrase, controlled tags, and bounded numeric features |

### Rights basis

The work was published in 1910. The linked Wikisource work page and Wikimedia Commons scan mark it as public domain. The dataset does not reproduce long passages; runtime meanings are short Korean paraphrases with a section locator.

### Normalization decisions

1. RWS card order is retained: Strength 8 and Justice 11.
2. Waite's wording is sometimes archaic, inconsistent, or contrary to common modern meanings. The source record is preserved rather than silently replaced with modern convention.
3. The Two of Cups entry in Part III §2 has no reversed line. Its reversed candidate is derived from the additional meaning in Part III §4 and is explicitly located there.
4. `polarity`, `action_level`, `speed_level`, `stability_level`, `ending_level`, Korean advice, warnings, and semantic tags are editorial derivations. They are not presented as Waite's own numerical system.
5. Page numbers are left empty because page numbering varies between the 1910 and 1922 printings. `source_locator` is the authoritative trace field.

## GOLDEN_DAWN_BOOK_T_1912

| Field | Value |
|---|---|
| Work | “A Description of the Cards of the Tarot with Their Attributions,” Liber LXXVIII / Book T material |
| Publication | *The Equinox*, Vol. I, No. 8 |
| Publication year | 1912 |
| Role | Golden Dawn titles, Hebrew letters, Tree paths, planets, zodiac signs, decans, Sephiroth, suit elements, and court elements |
| Primary scan | <https://100thmonkeypress.com/biblio/acrowley/books/equinox_1_8_1912/equinox_1_8_text.pdf> |
| Searchable transcription used for checking | <https://www.tarrdaniel.com/documents/Thelemagick/publication/english/Liber_LXXVIII.html> |
| Dataset transformation | Normalized table values only; no modern-edition prose copied |

### Rights basis

The material was published in 1912. The dataset stores normalized facts and short titles from the historical tables. It does not ingest commentary from modern commercial editions.

### Normalization decisions

1. Minor numbered cards 2–10 receive Golden Dawn title, planet, zodiac sign, decan, and Sephirah.
2. Aces receive suit element, Golden Dawn title, and `KETHER`.
3. RWS visual court labels are mapped to the Golden Dawn ranks as follows:
   - RWS Knight → Golden Dawn King/Knight → `FIRE`
   - RWS Queen → Golden Dawn Queen → `WATER`
   - RWS King → Golden Dawn Prince → `AIR`
   - RWS Page → Golden Dawn Princess/Knave → `EARTH`
4. Major Arcana retain RWS card numbering while using the traditional Hebrew-letter and path sequence.
5. Judgement stores Fire with an additional Spirit attribution. The World stores Saturn with Earth retained for elemental calculation.
6. Elemental dignity rules follow Book T:
   - same element strengthens;
   - Fire–Air, Fire–Earth, and Air–Water are friendly;
   - Fire–Water and Air–Earth are inimical;
   - Water–Earth is not explicitly declared friendly in this rule set and is treated as neutral.

## Relation rules

`relation_rules.csv` is a project-designed semantic transition grammar. Each row is marked:

```text
origin = DESIGNED
source_code = blank
source_locator = Editorial relation grammar v1
```

The rules therefore do not falsely claim that Waite or the Golden Dawn wrote specific modern transitions such as `ENDING → MOVEMENT`. Historical sources provide card meanings and correspondence systems; the software's reusable relationship grammar is an editorial engineering layer.

## Review procedure

1. Check that all 78 stable card codes are present.
2. Require exactly one upright and one reversed `GENERAL` meaning per card.
3. Require a source code, source locator, derivation type, review method, and review note for every meaning and correspondence.
4. Validate numeric ranges and foreign-key references.
5. Require exactly one primary tag per meaning.
6. Check Golden Dawn coverage by card class: Major, Ace, numbered pip, and court.
7. Reject relation rules that claim a historical source while marked `DESIGNED`.
8. Generate the CSV package deterministically and compare file hashes.
9. Load into both SQLite tests and PostgreSQL CI, then resolve all 78 cards in both orientations.

## Known limitation

This release is a source-traceable engine baseline, not a final scholarly critical edition. The Korean paraphrases and numeric features should be improved through golden-case evaluation while keeping the historical source fields immutable and reviewable.

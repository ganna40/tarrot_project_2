# Curated Tarot Knowledge v1

This directory is the review surface for the runtime PostgreSQL seed.

- `card_meanings.csv`: 156 Korean editorial paraphrases of Waite Part III (78 cards × upright/reversed).
- `card_correspondences.csv`: Golden Dawn / Book T titles and normalized correspondences.
- `card_meaning_tags.csv`: controlled semantic tags used by the rule engine.
- `relation_rules.csv`: transition grammar marked `origin=DESIGNED`; these rules are **not** historical-source claims.

Historical wording is not copied into the service response. `APPROVED` means the record passed the project source/structure/editorial review, not that a professional diviner or academic institution endorsed it.

Special decisions:

1. Two of Cups has no reversed line in Waite Part III §2; the reversed value is normalized from Part III §4.
2. RWS Strength=8 and Justice=11 are retained.
3. Court mapping follows the source-aware RWS visual labels: mounted Knight=Fire, Queen=Water, seated King=Golden Dawn Prince/Air, Page=Earth.
4. Judgement keeps Fire plus Spirit; World keeps Saturn plus Earth.
5. Major-card `ELEMENT` values are normalized for elemental-dignity calculation and do not replace the primary planet/zodiac/element attribution.

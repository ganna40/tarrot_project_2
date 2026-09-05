from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    pass


class Source(Base):
    __tablename__ = "sources"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    code: Mapped[str] = mapped_column(String(64), unique=True, index=True)
    title: Mapped[str] = mapped_column(String(255))
    author: Mapped[str | None] = mapped_column(String(255), nullable=True)
    publication_year: Mapped[int | None] = mapped_column(Integer, nullable=True)
    source_type: Mapped[str] = mapped_column(String(32))
    license_status: Mapped[str] = mapped_column(String(32))
    source_url: Mapped[str | None] = mapped_column(Text, nullable=True)
    rights_basis: Mapped[str | None] = mapped_column(Text, nullable=True)
    priority: Mapped[int] = mapped_column(Integer, default=100)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))


class TarotCard(Base):
    __tablename__ = "tarot_cards"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    code: Mapped[str] = mapped_column(String(64), unique=True, index=True)
    name_ko: Mapped[str] = mapped_column(String(100))
    name_en: Mapped[str] = mapped_column(String(100))
    arcana: Mapped[str] = mapped_column(String(16))
    suit: Mapped[str | None] = mapped_column(String(16), nullable=True)
    rank: Mapped[str | None] = mapped_column(String(16), nullable=True)
    number: Mapped[int | None] = mapped_column(Integer, nullable=True)
    sort_order: Mapped[int] = mapped_column(Integer, unique=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)


class CardMeaning(Base):
    __tablename__ = "card_meanings"
    __table_args__ = (
        UniqueConstraint("card_id", "source_id", "orientation", "context", name="uq_card_meaning_version"),
        CheckConstraint("polarity >= -5 AND polarity <= 5", name="ck_meaning_polarity"),
        CheckConstraint("action_level >= 0 AND action_level <= 5", name="ck_meaning_action"),
        CheckConstraint("speed_level >= 0 AND speed_level <= 5", name="ck_meaning_speed"),
        CheckConstraint("stability_level >= 0 AND stability_level <= 5", name="ck_meaning_stability"),
        CheckConstraint("ending_level >= 0 AND ending_level <= 5", name="ck_meaning_ending"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    card_id: Mapped[int] = mapped_column(ForeignKey("tarot_cards.id", ondelete="CASCADE"), index=True)
    source_id: Mapped[int] = mapped_column(ForeignKey("sources.id", ondelete="RESTRICT"), index=True)
    orientation: Mapped[str] = mapped_column(String(16), index=True)
    context: Mapped[str] = mapped_column(String(16), index=True)
    meaning_text: Mapped[str] = mapped_column(Text)
    advice_text: Mapped[str | None] = mapped_column(Text, nullable=True)
    warning_text: Mapped[str | None] = mapped_column(Text, nullable=True)
    polarity: Mapped[float] = mapped_column(Float)
    action_level: Mapped[float] = mapped_column(Float)
    speed_level: Mapped[float] = mapped_column(Float)
    stability_level: Mapped[float] = mapped_column(Float)
    ending_level: Mapped[float] = mapped_column(Float)
    origin: Mapped[str] = mapped_column(String(32), default="SOURCE")
    source_locator: Mapped[str | None] = mapped_column(String(255), nullable=True)
    page_start: Mapped[int | None] = mapped_column(Integer, nullable=True)
    page_end: Mapped[int | None] = mapped_column(Integer, nullable=True)
    priority: Mapped[int] = mapped_column(Integer, default=100)
    review_status: Mapped[str] = mapped_column(String(16), default="CANDIDATE", index=True)
    review_method: Mapped[str | None] = mapped_column(String(64), nullable=True)
    review_notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)


class InterpretationTag(Base):
    __tablename__ = "interpretation_tags"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    code: Mapped[str] = mapped_column(String(64), unique=True, index=True)
    name_ko: Mapped[str] = mapped_column(String(100))
    description: Mapped[str] = mapped_column(Text)


class CardMeaningTag(Base):
    __tablename__ = "card_meaning_tags"
    __table_args__ = (CheckConstraint("weight >= 0 AND weight <= 1", name="ck_card_tag_weight"),)

    card_meaning_id: Mapped[int] = mapped_column(
        ForeignKey("card_meanings.id", ondelete="CASCADE"), primary_key=True
    )
    tag_id: Mapped[int] = mapped_column(
        ForeignKey("interpretation_tags.id", ondelete="CASCADE"), primary_key=True
    )
    weight: Mapped[float] = mapped_column(Float, default=1.0)
    is_primary: Mapped[bool] = mapped_column(Boolean, default=False)


class CardCorrespondence(Base):
    __tablename__ = "card_correspondences"
    __table_args__ = (
        UniqueConstraint(
            "card_id", "source_id", "correspondence_type", "value", name="uq_card_correspondence"
        ),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    card_id: Mapped[int] = mapped_column(ForeignKey("tarot_cards.id", ondelete="CASCADE"), index=True)
    source_id: Mapped[int] = mapped_column(ForeignKey("sources.id", ondelete="RESTRICT"), index=True)
    correspondence_type: Mapped[str] = mapped_column(String(32), index=True)
    value: Mapped[str] = mapped_column(String(100))
    source_locator: Mapped[str | None] = mapped_column(String(255), nullable=True)
    page_start: Mapped[int | None] = mapped_column(Integer, nullable=True)
    page_end: Mapped[int | None] = mapped_column(Integer, nullable=True)
    priority: Mapped[int] = mapped_column(Integer, default=100)
    review_status: Mapped[str] = mapped_column(String(16), default="CANDIDATE")
    review_method: Mapped[str | None] = mapped_column(String(64), nullable=True)
    review_notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)


class RelationRule(Base):
    __tablename__ = "relation_rules"
    __table_args__ = (
        UniqueConstraint("from_tag_id", "to_tag_id", "context", "relation_type", name="uq_relation_rule"),
        CheckConstraint("score_delta >= -2 AND score_delta <= 2", name="ck_relation_score"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    from_tag_id: Mapped[int] = mapped_column(ForeignKey("interpretation_tags.id"), index=True)
    to_tag_id: Mapped[int] = mapped_column(ForeignKey("interpretation_tags.id"), index=True)
    context: Mapped[str | None] = mapped_column(String(16), nullable=True, index=True)
    relation_type: Mapped[str] = mapped_column(String(32))
    transition_text: Mapped[str] = mapped_column(Text)
    score_delta: Mapped[float] = mapped_column(Float, default=0.0)
    priority: Mapped[int] = mapped_column(Integer, default=100)
    source_id: Mapped[int | None] = mapped_column(ForeignKey("sources.id"), nullable=True)
    source_locator: Mapped[str | None] = mapped_column(String(255), nullable=True)
    page_start: Mapped[int | None] = mapped_column(Integer, nullable=True)
    page_end: Mapped[int | None] = mapped_column(Integer, nullable=True)
    origin: Mapped[str] = mapped_column(String(16), default="DESIGNED")
    review_status: Mapped[str] = mapped_column(String(16), default="CANDIDATE")
    review_method: Mapped[str | None] = mapped_column(String(64), nullable=True)
    review_notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)


class SpreadPosition(Base):
    __tablename__ = "spread_positions"
    __table_args__ = (UniqueConstraint("spread_code", "position_order", name="uq_spread_position"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    spread_code: Mapped[str] = mapped_column(String(32), index=True)
    position_order: Mapped[int] = mapped_column(Integer)
    label_ko: Mapped[str] = mapped_column(String(50))
    role: Mapped[str] = mapped_column(String(32))
    weight: Mapped[float] = mapped_column(Float)

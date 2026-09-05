from __future__ import annotations

from enum import Enum
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, field_validator


class ReadingContext(str, Enum):
    GENERAL = "GENERAL"
    LOVE = "LOVE"
    CAREER = "CAREER"
    BUSINESS = "BUSINESS"
    MONEY = "MONEY"
    TIMING = "TIMING"


class Orientation(str, Enum):
    UPRIGHT = "UPRIGHT"
    REVERSED = "REVERSED"


class Verdict(str, Enum):
    POSITIVE = "POSITIVE"
    CAUTIOUS = "CAUTIOUS"
    NEGATIVE = "NEGATIVE"


class ResponseLength(str, Enum):
    SHORT = "SHORT"
    NORMAL = "NORMAL"
    DETAILED = "DETAILED"


class CardInput(BaseModel):
    code: str = Field(min_length=1, max_length=64)
    orientation: Orientation = Orientation.UPRIGHT

    @field_validator("code")
    @classmethod
    def normalize_code(cls, value: str) -> str:
        return value.strip().upper().replace(" ", "_")


class ReadingRequest(BaseModel):
    question: str = Field(min_length=1, max_length=2000)
    context: str | None = Field(default=None, max_length=2000)
    reading_context: ReadingContext | None = None
    spread_type: str = "three_card"
    cards: list[CardInput] | None = None
    response_length: ResponseLength = ResponseLength.SHORT
    include_trace: bool = False
    use_llm: bool = True

    @field_validator("spread_type")
    @classmethod
    def validate_spread_type(cls, value: str) -> str:
        if value != "three_card":
            raise ValueError("v1은 three_card 스프레드만 지원합니다")
        return value


class ResolvedCard(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    code: str
    name_ko: str
    name_en: str
    orientation: Orientation
    position_order: int
    position_label: str
    meaning: str
    advice: str | None = None
    warning: str | None = None
    polarity: float = Field(ge=-5, le=5)
    action_level: float = Field(ge=0, le=5)
    speed_level: float = Field(ge=0, le=5)
    stability_level: float = Field(ge=0, le=5)
    ending_level: float = Field(ge=0, le=5)
    primary_tag: str
    tags: list[str]
    element: str | None = None
    source_code: str
    page_start: int | None = None
    page_end: int | None = None


class Transition(BaseModel):
    from_card: str
    to_card: str
    from_tag: str
    to_tag: str
    relation_type: str
    transition_text: str
    score_delta: float = 0.0
    rule_id: int | None = None


class InterpretationPlan(BaseModel):
    question: str
    reading_context: ReadingContext
    cards: list[ResolvedCard]
    transitions: list[Transition]
    elemental_modifier: float
    score: float
    verdict: Verdict
    flow_tags: list[str]
    flow_summary: str
    advice_constraints: list[str]


class ReadingResponse(BaseModel):
    spread_name: str = "3카드 흐름"
    spread_type: str = "three_card"
    reading_context: ReadingContext
    verdict: Verdict
    score: float
    flow_summary: str
    cards: list[ResolvedCard]
    overall_interpretation: str
    advice: str
    llm_used: bool
    trace: dict[str, Any] | None = None
    disclaimer: str = "타로 해석은 참고용이며 중요한 결정의 유일한 근거로 사용하지 마세요."

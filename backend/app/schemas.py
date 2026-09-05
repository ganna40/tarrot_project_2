from __future__ import annotations

import re
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


class LLMReasoningEffort(str, Enum):
    DEFAULT = "DEFAULT"
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    XHIGH = "XHIGH"


class InterpretationStyle(str, Enum):
    PRECISE = "PRECISE"
    BALANCED = "BALANCED"
    RICH = "RICH"


class InterpretationOptions(BaseModel):
    model: str | None = Field(default=None, max_length=128)
    reasoning_effort: LLMReasoningEffort = LLMReasoningEffort.DEFAULT
    style: InterpretationStyle = InterpretationStyle.BALANCED

    @field_validator("model")
    @classmethod
    def normalize_model(cls, value: str | None) -> str | None:
        if value is None:
            return None
        normalized = value.strip()
        if not normalized:
            return None
        if not re.fullmatch(r"[A-Za-z0-9._:-]+", normalized):
            raise ValueError("LLM 모델 ID에는 영문, 숫자, 점, 밑줄, 콜론, 하이픈만 사용할 수 있습니다")
        return normalized


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
    llm_model: str | None = Field(default=None, max_length=128)
    llm_reasoning_effort: LLMReasoningEffort = LLMReasoningEffort.DEFAULT
    interpretation_style: InterpretationStyle = InterpretationStyle.BALANCED

    @field_validator("spread_type")
    @classmethod
    def validate_spread_type(cls, value: str) -> str:
        if value != "three_card":
            raise ValueError("v1은 three_card 스프레드만 지원합니다")
        return value

    @field_validator("llm_model")
    @classmethod
    def normalize_llm_model(cls, value: str | None) -> str | None:
        return InterpretationOptions.normalize_model(value)

    def interpretation_options(self) -> InterpretationOptions:
        return InterpretationOptions(
            model=self.llm_model,
            reasoning_effort=self.llm_reasoning_effort,
            style=self.interpretation_style,
        )


class ResolvedCard(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    code: str
    name_ko: str
    name_en: str
    orientation: Orientation
    position_order: int
    position_label: str
    position_weight: float = Field(gt=0, le=20)
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
    source_url: str | None = None
    source_locator: str | None = None
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
    follow_up_questions: list[str] = Field(default_factory=list, min_length=3, max_length=3)
    llm_used: bool
    llm_model: str | None = None
    llm_reasoning_effort: LLMReasoningEffort = LLMReasoningEffort.DEFAULT
    interpretation_style: InterpretationStyle = InterpretationStyle.BALANCED
    trace: dict[str, Any] | None = None
    disclaimer: str = "타로 해석은 참고용이며 중요한 결정의 유일한 근거로 사용하지 마세요."

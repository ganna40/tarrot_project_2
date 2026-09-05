from __future__ import annotations

import json
from typing import Any

from app.config import Settings, get_settings
from app.schemas import (
    InterpretationOptions,
    InterpretationPlan,
    InterpretationStyle,
    LLMReasoningEffort,
    ResponseLength,
)


_BASE_OUTPUT_TOKENS = {
    ResponseLength.SHORT: 320,
    ResponseLength.NORMAL: 700,
    ResponseLength.DETAILED: 1200,
}

_STYLE_VERBOSITY = {
    InterpretationStyle.PRECISE: "low",
    InterpretationStyle.BALANCED: "medium",
    InterpretationStyle.RICH: "high",
}

_STYLE_INSTRUCTIONS = {
    InterpretationStyle.PRECISE: "핵심 결론과 카드 사이의 인과 흐름을 선명하게 설명하고 반복을 줄인다.",
    InterpretationStyle.BALANCED: "카드 사이의 변화, 질문자의 상황, 현실적인 시사점을 균형 있게 연결한다.",
    InterpretationStyle.RICH: (
        "카드 사이의 상징적 전환, 심리적 흐름, 현실 상황에서의 의미와 긴장·보완 관계를 하나의 이야기처럼 풍부하게 연결한다. "
        "창의성은 표현과 연결 해석에만 사용하고 DATA 밖의 사건·시기·인물·금액·확정적 미래를 만들지 않는다."
    ),
}


class OpenAIInterpretationService:
    """Use OpenAI only to verbalize an already-determined interpretation plan."""

    def __init__(self, settings: Settings | None = None, client: Any | None = None):
        self.settings = settings or get_settings()
        self._client = client

    def _get_client(self) -> Any:
        if self._client is not None:
            return self._client
        if not self.settings.openai_api_key:
            raise RuntimeError("OPENAI_API_KEY가 설정되지 않았습니다")
        try:
            from openai import OpenAI
        except ImportError as exc:  # pragma: no cover - exercised in deployed runtime
            raise RuntimeError("openai 패키지가 설치되지 않았습니다") from exc

        self._client = OpenAI(
            api_key=self.settings.openai_api_key,
            timeout=self.settings.openai_timeout_seconds,
        )
        return self._client

    def generate(
        self,
        plan: InterpretationPlan,
        response_length: ResponseLength,
        options: InterpretationOptions | None = None,
    ) -> str:
        effective_options = options or InterpretationOptions()
        model = effective_options.model or self.settings.openai_model
        if not model:
            raise RuntimeError("OPENAI_MODEL이 설정되지 않았습니다")

        payload = {
            "question": plan.question,
            "reading_context": plan.reading_context.value,
            "verdict": plan.verdict.value,
            "score": plan.score,
            "flow_summary": plan.flow_summary,
            "cards": [
                {
                    "code": card.code,
                    "position": card.position_label,
                    "orientation": card.orientation.value,
                    "meaning": card.meaning,
                    "primary_tag": card.primary_tag,
                    "tags": card.tags,
                    "element": card.element,
                    "advice": card.advice,
                }
                for card in plan.cards
            ],
            "transitions": [transition.model_dump(mode="json") for transition in plan.transitions],
            "allowed_advice": plan.advice_constraints,
        }

        request: dict[str, Any] = {
            "model": model,
            "instructions": (
                "당신은 타로 규칙 엔진이 확정한 해석 계획을 자연스러운 한국어로 편집하는 역할이다. "
                "verdict, score, flow_summary를 바꾸거나 반대 결론을 만들지 않는다. "
                "카드 뜻을 따로 나열하지 말고 카드 사이의 흐름을 중심으로 쓴다. "
                "제공되지 않은 사건을 만들어내거나 미래를 확정적으로 단정하지 않는다. "
                "의료·법률·투자 전문 조언을 하지 않는다. 마크다운 제목과 표는 사용하지 않는다. "
                f"{_STYLE_INSTRUCTIONS[effective_options.style]}"
            ),
            "input": json.dumps(payload, ensure_ascii=False),
            "max_output_tokens": _BASE_OUTPUT_TOKENS[response_length],
            "text": {"verbosity": _STYLE_VERBOSITY[effective_options.style]},
        }
        if effective_options.reasoning_effort is not LLMReasoningEffort.DEFAULT:
            request["reasoning"] = {"effort": effective_options.reasoning_effort.value.lower()}

        response = self._get_client().responses.create(**request)
        text = (response.output_text or "").strip()
        if not text:
            raise RuntimeError("OpenAI가 빈 응답을 반환했습니다")
        return text

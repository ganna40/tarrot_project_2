from __future__ import annotations

from typing import Protocol

from app.codex_service import CodexCLIInterpretationService
from app.config import Settings, get_settings
from app.openai_service import OpenAIInterpretationService
from app.schemas import InterpretationOptions, InterpretationPlan, ResponseLength


class InterpretationService(Protocol):
    def generate(
        self,
        plan: InterpretationPlan,
        response_length: ResponseLength,
        options: InterpretationOptions | None = None,
    ) -> str: ...


def build_interpretation_service(settings: Settings | None = None) -> InterpretationService:
    settings = settings or get_settings()
    provider = settings.llm_provider.strip().lower()

    if provider in {"codex_subscription", "codex"}:
        return CodexCLIInterpretationService(settings=settings)
    if provider in {"openai_api", "openai"}:
        return OpenAIInterpretationService(settings=settings)

    raise RuntimeError(f"지원하지 않는 LLM_PROVIDER입니다: {settings.llm_provider}")

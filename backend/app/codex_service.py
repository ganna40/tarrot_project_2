from __future__ import annotations

import json
import shutil
import subprocess
import tempfile
from pathlib import Path
from typing import Any, Callable

from app.config import Settings, get_settings
from app.schemas import (
    InterpretationOptions,
    InterpretationPlan,
    InterpretationStyle,
    LLMReasoningEffort,
    ResponseLength,
)


_STYLE_VERBOSITY = {
    InterpretationStyle.PRECISE: "low",
    InterpretationStyle.BALANCED: "medium",
    InterpretationStyle.RICH: "high",
}

_STYLE_INSTRUCTIONS = {
    InterpretationStyle.PRECISE: (
        "핵심 결론과 카드 사이의 인과 흐름을 선명하게 설명한다. 반복과 수사는 줄이고 현실적인 의미를 우선한다."
    ),
    InterpretationStyle.BALANCED: (
        "카드 사이의 변화, 질문자의 상황, 현실적인 시사점을 균형 있게 연결한다. 의미를 확장하되 DATA 밖으로 나가지 않는다."
    ),
    InterpretationStyle.RICH: (
        "해석을 풍부하게 전개한다. 카드 사이의 상징적 전환, 심리적 흐름, 현실 상황에서의 의미, 서로 긴장하거나 보완하는 지점을 "
        "하나의 이야기처럼 연결한다. 같은 말을 반복하지 말고 여러 층위의 의미를 보여준다. 다만 DATA 밖의 사건, 시기, 인물, 금액, "
        "확정적 미래를 새로 만들어내지 않는다. 창의성은 표현과 연결 해석에만 사용한다."
    ),
}


def _length_instruction(response_length: ResponseLength, style: InterpretationStyle) -> str:
    if style is InterpretationStyle.RICH:
        return {
            ResponseLength.SHORT: "한국어 약 5~7문장으로 쓰되 각 문장에 충분한 의미를 담는다.",
            ResponseLength.NORMAL: "한국어 약 9~13문장으로 흐름과 맥락을 충분히 설명한다.",
            ResponseLength.DETAILED: "한국어 약 12~18문장으로 상징, 심리, 현실적 의미를 충분히 풀어 설명한다.",
        }[response_length]
    return {
        ResponseLength.SHORT: "한국어 약 4~6문장으로 간결하게 작성한다.",
        ResponseLength.NORMAL: "한국어 약 7~10문장으로 작성한다.",
        ResponseLength.DETAILED: "한국어 약 10~15문장으로 충분히 설명한다.",
    }[response_length]


class CodexCLIInterpretationService:
    """Use the locally authenticated Codex CLI only to verbalize an engine plan.

    The caller is expected to have authenticated the CLI separately with
    `codex login`. No ChatGPT credential is read or stored by this application.
    """

    def __init__(
        self,
        settings: Settings | None = None,
        runner: Callable[..., Any] = subprocess.run,
        executable_resolver: Callable[[str], str | None] = shutil.which,
    ) -> None:
        self.settings = settings or get_settings()
        self._runner = runner
        self._executable_resolver = executable_resolver

    def _resolve_executable(self) -> str:
        executable = self._executable_resolver(self.settings.codex_executable)
        if not executable:
            raise RuntimeError(
                "Codex CLI를 찾을 수 없습니다. Codex CLI를 설치한 뒤 `codex --version`과 `codex login status`를 확인하세요."
            )
        return executable

    @staticmethod
    def _payload(plan: InterpretationPlan) -> dict[str, Any]:
        return {
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
                    "warning": card.warning,
                }
                for card in plan.cards
            ],
            "transitions": [transition.model_dump(mode="json") for transition in plan.transitions],
            "allowed_advice": plan.advice_constraints,
        }

    def _prompt(
        self,
        plan: InterpretationPlan,
        response_length: ResponseLength,
        options: InterpretationOptions,
    ) -> str:
        payload = json.dumps(self._payload(plan), ensure_ascii=False, indent=2)
        return (
            "당신은 타로 규칙 엔진이 이미 확정한 해석 계획을 자연스러운 한국어로 문장화하는 편집자다.\n"
            "아래 DATA를 유일한 해석 근거로 사용한다.\n"
            "verdict, score, flow_summary를 바꾸거나 반대 결론을 만들지 않는다.\n"
            "카드 뜻을 따로 나열하지 말고 카드 사이의 변화와 전체 흐름을 중심으로 쓴다.\n"
            "제공되지 않은 사건을 만들어내거나 미래를 확정적으로 단정하지 않는다.\n"
            "의료·법률·투자 전문 조언을 하지 않는다.\n"
            f"해설 스타일: {_STYLE_INSTRUCTIONS[options.style]}\n"
            f"분량: {_length_instruction(response_length, options.style)}\n"
            "파일을 읽거나 수정하거나 다른 도구를 사용할 필요가 없다. 최종 해석 문장만 출력한다.\n\n"
            f"DATA:\n{payload}"
        )

    def generate(
        self,
        plan: InterpretationPlan,
        response_length: ResponseLength,
        options: InterpretationOptions | None = None,
    ) -> str:
        executable = self._resolve_executable()
        effective_options = options or InterpretationOptions()
        prompt = self._prompt(plan, response_length, effective_options)
        effective_model = effective_options.model or self.settings.codex_model

        with tempfile.TemporaryDirectory(prefix="tarot-codex-") as temp_dir:
            output_path = Path(temp_dir) / "last-message.txt"
            command = [
                executable,
                "--ask-for-approval",
                "never",
            ]
            if effective_options.reasoning_effort is not LLMReasoningEffort.DEFAULT:
                command.extend(
                    [
                        "-c",
                        f'model_reasoning_effort="{effective_options.reasoning_effort.value.lower()}"',
                    ]
                )
            command.extend(
                [
                    "-c",
                    f'model_verbosity="{_STYLE_VERBOSITY[effective_options.style]}"',
                    "exec",
                    "--ephemeral",
                    "--sandbox",
                    "read-only",
                    "--skip-git-repo-check",
                    "--color",
                    "never",
                    "--output-last-message",
                    str(output_path),
                ]
            )
            if effective_model:
                command.extend(["--model", effective_model])
            command.append("-")

            completed = self._runner(
                command,
                input=prompt,
                text=True,
                encoding="utf-8",
                capture_output=True,
                timeout=self.settings.codex_timeout_seconds,
                cwd=temp_dir,
                check=False,
            )

            if completed.returncode != 0:
                detail = (completed.stderr or completed.stdout or "Codex CLI 실행 실패").strip()
                if len(detail) > 1000:
                    detail = detail[-1000:]
                raise RuntimeError(f"Codex CLI 실행에 실패했습니다: {detail}")

            if not output_path.exists():
                raise RuntimeError("Codex CLI가 최종 응답 파일을 생성하지 않았습니다")

            text = output_path.read_text(encoding="utf-8").strip()
            if not text:
                raise RuntimeError("Codex CLI가 빈 응답을 반환했습니다")
            return text

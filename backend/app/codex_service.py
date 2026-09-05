from __future__ import annotations

import json
import shutil
import subprocess
import tempfile
from pathlib import Path
from typing import Any, Callable

from app.config import Settings, get_settings
from app.schemas import InterpretationPlan, ResponseLength


_LENGTH_INSTRUCTIONS = {
    ResponseLength.SHORT: "한국어 약 4~6문장으로 간결하게 작성한다.",
    ResponseLength.NORMAL: "한국어 약 7~10문장으로 작성한다.",
    ResponseLength.DETAILED: "한국어 약 10~15문장으로 충분히 설명한다.",
}


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
                    "advice": card.advice,
                }
                for card in plan.cards
            ],
            "transitions": [transition.model_dump(mode="json") for transition in plan.transitions],
            "allowed_advice": plan.advice_constraints,
        }

    def _prompt(self, plan: InterpretationPlan, response_length: ResponseLength) -> str:
        payload = json.dumps(self._payload(plan), ensure_ascii=False, indent=2)
        return (
            "당신은 타로 규칙 엔진이 이미 확정한 해석 계획을 자연스러운 한국어로 문장화하는 편집자다.\n"
            "아래 DATA를 유일한 해석 근거로 사용한다.\n"
            "verdict, score, flow_summary를 바꾸거나 반대 결론을 만들지 않는다.\n"
            "카드 뜻을 따로 나열하지 말고 카드 사이의 변화와 전체 흐름을 중심으로 쓴다.\n"
            "제공되지 않은 사건을 만들어내거나 미래를 확정적으로 단정하지 않는다.\n"
            "의료·법률·투자 전문 조언을 하지 않는다.\n"
            "파일을 읽거나 수정하거나 다른 도구를 사용할 필요가 없다. 최종 해석 문장만 출력한다.\n"
            f"{_LENGTH_INSTRUCTIONS[response_length]}\n\n"
            f"DATA:\n{payload}"
        )

    def generate(self, plan: InterpretationPlan, response_length: ResponseLength) -> str:
        executable = self._resolve_executable()
        prompt = self._prompt(plan, response_length)

        with tempfile.TemporaryDirectory(prefix="tarot-codex-") as temp_dir:
            output_path = Path(temp_dir) / "last-message.txt"
            command = [
                executable,
                "exec",
                "--ephemeral",
                "--sandbox",
                "read-only",
                "--ask-for-approval",
                "never",
                "--skip-git-repo-check",
                "--color",
                "never",
                "--output-last-message",
                str(output_path),
            ]
            if self.settings.codex_model:
                command.extend(["--model", self.settings.codex_model])
            command.append("-")

            completed = self._runner(
                command,
                input=prompt,
                text=True,
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

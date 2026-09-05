from __future__ import annotations

import subprocess
from pathlib import Path

import pytest

from app.config import Settings
from app.schemas import (
    InterpretationPlan,
    Orientation,
    ReadingContext,
    ResolvedCard,
    ResponseLength,
    Verdict,
)


def sample_plan() -> InterpretationPlan:
    cards = [
        ResolvedCard(
            code="TEN_OF_SWORDS",
            name_ko="소드 10",
            name_en="Ten of Swords",
            orientation=Orientation.UPRIGHT,
            position_order=1,
            position_label="시작",
            position_weight=1.0,
            meaning="기존 국면의 종료",
            advice="끝난 부분을 정리한다.",
            polarity=-3,
            action_level=1,
            speed_level=1,
            stability_level=1,
            ending_level=5,
            primary_tag="ENDING",
            tags=["ENDING", "LOSS"],
            element="AIR",
            source_code="WAITE_PKD_1910",
        ),
        ResolvedCard(
            code="EIGHT_OF_WANDS",
            name_ko="완드 8",
            name_en="Eight of Wands",
            orientation=Orientation.UPRIGHT,
            position_order=2,
            position_label="전개",
            position_weight=1.0,
            meaning="빠른 진행",
            advice="움직임이 생길 때 대응한다.",
            polarity=3,
            action_level=5,
            speed_level=5,
            stability_level=2,
            ending_level=0,
            primary_tag="MOVEMENT",
            tags=["MOVEMENT", "SPEED"],
            element="FIRE",
            source_code="WAITE_PKD_1910",
        ),
        ResolvedCard(
            code="HIEROPHANT",
            name_ko="교황",
            name_en="The Hierophant",
            orientation=Orientation.UPRIGHT,
            position_order=3,
            position_label="결과",
            position_weight=1.0,
            meaning="공식화와 제도적 절차",
            advice="조건과 절차를 문서화한다.",
            polarity=2,
            action_level=2,
            speed_level=2,
            stability_level=5,
            ending_level=0,
            primary_tag="FORMALIZATION",
            tags=["FORMALIZATION", "AUTHORITY"],
            element="EARTH",
            source_code="WAITE_PKD_1910",
        ),
    ]
    return InterpretationPlan(
        question="게임을 만들면 실제 투자로 이어질까?",
        reading_context=ReadingContext.BUSINESS,
        cards=cards,
        transitions=[],
        elemental_modifier=0.0,
        score=1.5,
        verdict=Verdict.POSITIVE,
        flow_tags=["ENDING", "MOVEMENT", "FORMALIZATION"],
        flow_summary="기존 단계가 끝나고 빠르게 움직인 뒤 계약과 절차로 공식화되는 흐름",
        advice_constraints=["데모를 먼저 완성한다", "투자 조건을 문서화한다"],
    )


def test_codex_subscription_service_runs_safe_ephemeral_exec_and_reads_final_message(tmp_path):
    from app.codex_service import CodexCLIInterpretationService

    captured: dict[str, object] = {}

    def fake_runner(command, **kwargs):
        captured["command"] = command
        captured["kwargs"] = kwargs
        output_path = Path(command[command.index("--output-last-message") + 1])
        output_path.write_text("종료 뒤 빠르게 진행되고, 마지막에는 계약으로 공식화되는 흐름입니다.", encoding="utf-8")
        return subprocess.CompletedProcess(command, 0, stdout="", stderr="")

    settings = Settings(
        llm_provider="codex_subscription",
        codex_executable="codex",
        codex_model="test-model",
        codex_timeout_seconds=12,
    )
    service = CodexCLIInterpretationService(
        settings=settings,
        runner=fake_runner,
        executable_resolver=lambda _: "C:/tools/codex.exe",
    )

    result = service.generate(sample_plan(), ResponseLength.SHORT)

    assert result.startswith("종료 뒤 빠르게")
    command = captured["command"]
    assert command[0] == "C:/tools/codex.exe"
    assert command[1:3] == ["--ask-for-approval", "never"]
    assert command[3] == "exec"
    assert "--ephemeral" in command
    assert command[command.index("--sandbox") + 1] == "read-only"
    assert command[command.index("--model") + 1] == "test-model"
    assert command[-1] == "-"
    kwargs = captured["kwargs"]
    assert kwargs["input"].find("기존 단계가 끝나고 빠르게 움직인 뒤") >= 0
    assert kwargs["input"].find("카드 뜻을 따로 나열하지") >= 0
    assert kwargs["encoding"] == "utf-8"
    assert kwargs["timeout"] == 12


def test_codex_subscription_service_reports_missing_cli():
    from app.codex_service import CodexCLIInterpretationService

    service = CodexCLIInterpretationService(
        settings=Settings(llm_provider="codex_subscription", codex_executable="codex"),
        executable_resolver=lambda _: None,
    )

    with pytest.raises(RuntimeError, match="Codex CLI"):
        service.generate(sample_plan(), ResponseLength.SHORT)


def test_provider_factory_selects_codex_subscription():
    from app.codex_service import CodexCLIInterpretationService
    from app.interpretation_service import build_interpretation_service

    service = build_interpretation_service(Settings(llm_provider="codex_subscription"))
    assert isinstance(service, CodexCLIInterpretationService)

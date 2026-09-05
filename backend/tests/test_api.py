from __future__ import annotations

from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.main import create_app
from app.models import Base
from app.seed import seed_public_domain_knowledge


class FakeOpenAIService:
    def generate(self, plan, response_length, options=None):
        return "엔진이 확정한 흐름을 유지한 테스트용 문장입니다."


class FailingOpenAIService:
    def generate(self, plan, response_length, options=None):
        raise RuntimeError("simulated failure")


class CapturingInterpretationService:
    def __init__(self):
        self.options = None

    def generate(self, plan, response_length, options=None):
        self.options = options
        return "요청별 AI 설정이 적용된 테스트 해석입니다."


def build_client(openai_service=None, api_access_key=None) -> TestClient:
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(engine)
    factory = sessionmaker(engine, expire_on_commit=False)
    with factory() as session:
        seed_public_domain_knowledge(session)
        session.commit()
    app = create_app(
        session_factory=factory,
        openai_service=openai_service,
        run_startup_seed=False,
        api_access_key=api_access_key,
    )
    return TestClient(app)


def known_request(**overrides):
    payload = {
        "question": "게임을 만들면 투자를 받을 수 있을까?",
        "context": "투자자가 데모를 보면 검토한다고 말했다.",
        "reading_context": "BUSINESS",
        "spread_type": "three_card",
        "cards": [
            {"code": "TEN_OF_SWORDS", "orientation": "UPRIGHT"},
            {"code": "EIGHT_OF_WANDS", "orientation": "UPRIGHT"},
            {"code": "HIEROPHANT", "orientation": "UPRIGHT"},
        ],
        "response_length": "SHORT",
        "include_trace": True,
        "use_llm": False,
    }
    payload.update(overrides)
    return payload


def test_health_endpoint():
    with build_client() as client:
        response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "healthy"


def test_known_reading_returns_deterministic_flow_and_trace():
    with build_client() as client:
        response = client.post("/api/v1/readings", json=known_request())

    assert response.status_code == 200
    body = response.json()
    assert body["reading_context"] == "BUSINESS"
    assert body["verdict"] == "POSITIVE"
    assert "계약과 절차" in body["flow_summary"]
    assert body["llm_used"] is False
    assert [item["relation_type"] for item in body["trace"]["transitions"]] == ["ACCELERATE", "FORMALIZE"]
    assert body["trace"]["cards"][0]["source_code"] == "WAITE_PKD_1910"
    assert body["trace"]["cards"][0]["source_locator"] == "Part III §2 — Swords, Ten"


def test_openai_text_does_not_change_engine_fields():
    with build_client(FakeOpenAIService()) as client:
        with_llm = client.post("/api/v1/readings", json=known_request(use_llm=True)).json()
    with build_client() as client:
        without_llm = client.post("/api/v1/readings", json=known_request(use_llm=False)).json()

    assert with_llm["llm_used"] is True
    assert with_llm["overall_interpretation"].startswith("엔진이 확정한")
    for field in ("reading_context", "verdict", "score", "flow_summary"):
        assert with_llm[field] == without_llm[field]


def test_reading_passes_per_request_model_reasoning_and_style_to_interpretation_service():
    service = CapturingInterpretationService()
    payload = known_request(
        use_llm=True,
        response_length="DETAILED",
        llm_model="gpt-5.6-sol",
        llm_reasoning_effort="XHIGH",
        interpretation_style="RICH",
    )

    with build_client(service) as client:
        response = client.post("/api/v1/readings", json=payload)

    assert response.status_code == 200
    body = response.json()
    assert body["llm_used"] is True
    assert body["llm_model"] == "gpt-5.6-sol"
    assert body["llm_reasoning_effort"] == "XHIGH"
    assert body["interpretation_style"] == "RICH"
    assert service.options.model == "gpt-5.6-sol"
    assert service.options.reasoning_effort.value == "XHIGH"
    assert service.options.style.value == "RICH"


def test_openai_failure_uses_rule_based_fallback():
    with build_client(FailingOpenAIService()) as client:
        response = client.post("/api/v1/readings", json=known_request(use_llm=True))

    assert response.status_code == 200
    assert response.json()["llm_used"] is False
    assert response.json()["overall_interpretation"]


def test_duplicate_card_request_returns_422():
    payload = known_request()
    payload["cards"][1]["code"] = "TEN_OF_SWORDS"
    with build_client() as client:
        response = client.post("/api/v1/readings", json=payload)

    assert response.status_code == 422
    assert response.json()["error"] == "INVALID_CARDS"


def test_formerly_unsupported_card_is_available():
    payload = known_request()
    payload["cards"] = [
        {"code": "FOOL", "orientation": "UPRIGHT"},
        {"code": "TWO_OF_CUPS", "orientation": "UPRIGHT"},
        {"code": "WORLD", "orientation": "UPRIGHT"},
    ]
    with build_client() as client:
        response = client.post("/api/v1/readings", json=payload)

    assert response.status_code == 200
    assert [card["code"] for card in response.json()["cards"]] == ["FOOL", "TWO_OF_CUPS", "WORLD"]


def test_server_can_draw_three_supported_cards():
    with build_client() as client:
        response = client.post("/api/v1/readings", json=known_request(cards=None, include_trace=False))

    assert response.status_code == 200
    assert len(response.json()["cards"]) == 3


def test_github_pages_origin_is_allowed_by_cors():
    with build_client() as client:
        response = client.options(
            "/api/v1/readings",
            headers={
                "Origin": "https://ganna40.github.io",
                "Access-Control-Request-Method": "POST",
            },
        )

    assert response.status_code == 200
    assert response.headers["access-control-allow-origin"] == "https://ganna40.github.io"


def test_static_validator_compatibility_endpoint():
    with build_client() as client:
        response = client.post("/api/consultation", json=known_request())

    assert response.status_code == 200
    assert response.json()["verdict"] == "POSITIVE"


def test_x_api_key_header_is_allowed_by_cors():
    with build_client() as client:
        response = client.options(
            "/api/v1/readings",
            headers={
                "Origin": "https://ganna40.github.io",
                "Access-Control-Request-Method": "POST",
                "Access-Control-Request-Headers": "X-API-Key",
            },
        )

    assert response.status_code == 200
    assert "x-api-key" in response.headers["access-control-allow-headers"].lower()


def test_optional_api_access_key_accepts_bearer_and_x_api_key():
    with build_client(api_access_key="test-secret") as client:
        missing = client.post("/api/v1/readings", json=known_request())
        bearer = client.post(
            "/api/v1/readings",
            json=known_request(),
            headers={"Authorization": "Bearer test-secret"},
        )
        x_key = client.post(
            "/api/v1/readings",
            json=known_request(),
            headers={"X-API-Key": "test-secret"},
        )

    assert missing.status_code == 401
    assert bearer.status_code == 200
    assert x_key.status_code == 200

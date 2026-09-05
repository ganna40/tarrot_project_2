from __future__ import annotations

import hmac
import logging
from collections.abc import Generator
from contextlib import asynccontextmanager
from typing import Any, Protocol

from fastapi import Depends, FastAPI, Header, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session, sessionmaker

from app.config import get_settings
from app.database import close_database, get_session, init_database
from app.engine import calculate_reading, classify_context, validate_card_inputs
from app.fallback import build_advice, build_fallback_interpretation
from app.openai_service import OpenAIInterpretationService
from app.repository import KnowledgeNotReadyError, TarotRepository
from app.schemas import ReadingRequest, ReadingResponse, ResponseLength
from app.seed import seed_demo_knowledge

logger = logging.getLogger(__name__)


class InterpretationService(Protocol):
    def generate(self, plan: Any, response_length: ResponseLength) -> str: ...


def create_app(
    session_factory: sessionmaker[Session] | None = None,
    openai_service: InterpretationService | None = None,
    run_startup_seed: bool = True,
    api_access_key: str | None = None,
) -> FastAPI:
    settings = get_settings()
    service = openai_service or OpenAIInterpretationService(settings=settings)
    effective_access_key = api_access_key or settings.api_access_key

    @asynccontextmanager
    async def lifespan(_app: FastAPI):
        if session_factory is None:
            init_database()

        if run_startup_seed and settings.auto_seed_demo:
            if session_factory is not None:
                with session_factory() as session:
                    seed_demo_knowledge(session)
                    session.commit()
            else:
                session_generator = get_session()
                session = next(session_generator)
                try:
                    seed_demo_knowledge(session)
                    session.commit()
                finally:
                    session_generator.close()
        yield
        if session_factory is None:
            close_database()

    app = FastAPI(
        title=settings.app_name,
        version="1.0.0",
        description="Deterministic three-card tarot interpretation engine",
        lifespan=lifespan,
    )
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=False,
        allow_methods=["GET", "POST", "OPTIONS"],
        allow_headers=["Content-Type", "Authorization", "X-API-Key"],
    )

    def session_dependency() -> Generator[Session, None, None]:
        if session_factory is not None:
            with session_factory() as session:
                yield session
            return
        yield from get_session()

    def require_access(
        authorization: str | None = Header(default=None),
        x_api_key: str | None = Header(default=None),
    ) -> None:
        if not effective_access_key:
            return
        bearer = ""
        if authorization and authorization.lower().startswith("bearer "):
            bearer = authorization[7:].strip()
        candidate = x_api_key or bearer
        if not candidate or not hmac.compare_digest(candidate, effective_access_key):
            raise HTTPException(status_code=401, detail="Invalid or missing API access key")

    @app.get("/health")
    def health() -> dict[str, str]:
        return {"status": "healthy", "app": settings.app_name, "version": "1.0.0"}

    @app.post("/api/consultation", response_model=ReadingResponse, include_in_schema=False)
    @app.post("/api/v1/readings", response_model=ReadingResponse)
    def create_reading(
        request: ReadingRequest,
        session: Session = Depends(session_dependency),
        _access: None = Depends(require_access),
    ) -> ReadingResponse | JSONResponse:
        repository = TarotRepository(session)
        card_inputs = request.cards or repository.draw_supported_cards(3)

        try:
            validate_card_inputs(card_inputs)
        except ValueError as exc:
            return JSONResponse(
                status_code=422,
                content={"error": "INVALID_CARDS", "message": str(exc)},
            )

        reading_context = request.reading_context or classify_context(request.question, request.context)
        try:
            cards = repository.resolve_cards(card_inputs, reading_context)
            transitions = repository.resolve_transitions(cards, reading_context)
            elemental_modifier = repository.elemental_modifier(cards)
        except KnowledgeNotReadyError as exc:
            return JSONResponse(
                status_code=503,
                content={"error": "KNOWLEDGE_NOT_READY", "message": str(exc)},
            )

        plan = calculate_reading(
            question=request.question,
            reading_context=reading_context,
            cards=cards,
            transitions=transitions,
            elemental_modifier=elemental_modifier,
        )

        overall_interpretation = build_fallback_interpretation(plan, request.response_length)
        llm_used = False
        if request.use_llm:
            try:
                generated = service.generate(plan, request.response_length).strip()
                if generated:
                    overall_interpretation = generated
                    llm_used = True
            except Exception as exc:
                logger.warning("OpenAI interpretation failed; fallback used: %s", exc)

        trace = None
        if request.include_trace:
            trace = {
                "flow_tags": plan.flow_tags,
                "elemental_modifier": plan.elemental_modifier,
                "transitions": [transition.model_dump(mode="json") for transition in plan.transitions],
                "cards": [
                    {
                        "code": card.code,
                        "meaning": card.meaning,
                        "primary_tag": card.primary_tag,
                        "tags": card.tags,
                        "element": card.element,
                        "source_code": card.source_code,
                        "page_start": card.page_start,
                        "page_end": card.page_end,
                    }
                    for card in plan.cards
                ],
            }

        return ReadingResponse(
            reading_context=plan.reading_context,
            verdict=plan.verdict,
            score=plan.score,
            flow_summary=plan.flow_summary,
            cards=plan.cards,
            overall_interpretation=overall_interpretation,
            advice=build_advice(plan),
            llm_used=llm_used,
            trace=trace,
        )

    return app


app = create_app()

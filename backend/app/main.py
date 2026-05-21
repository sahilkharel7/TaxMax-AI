from typing import Optional

from fastapi import FastAPI, Query
from fastapi.middleware.cors import CORSMiddleware

from app.config import get_settings
from app.schemas import (
    ChatRequest,
    ChatResponse,
    HealthResponse,
    TaxAnalysisResponse,
    TaxScenarioRequest,
)
from app.services.analysis_service import analyze_scenario
from app.services.chat_service import generate_chat_reply
from app.services.tax_rule_service import get_tax_rule_context_dict


def create_app() -> FastAPI:
    settings = get_settings()

    app = FastAPI(title=settings.app_name)

    app.add_middleware(
        CORSMiddleware,
        allow_origins=[
            "http://localhost:3000",
            "http://localhost:5173",
            "http://127.0.0.1:3000",
            "http://127.0.0.1:5173",
        ],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    @app.get("/api/health", response_model=HealthResponse)
    def health_check() -> HealthResponse:
        return HealthResponse(status="ok", service=settings.app_name)

    @app.post("/api/chat", response_model=ChatResponse)
    def chat(request: ChatRequest) -> ChatResponse:
        return generate_chat_reply(request)

    @app.post("/api/tax/analyze", response_model=TaxAnalysisResponse)
    def analyze(request: TaxScenarioRequest) -> TaxAnalysisResponse:
        return analyze_scenario(request)

    @app.get("/api/tax/rules")
    def tax_rules(
        tax_year: int = Query(..., ge=2000, le=2100, description="Tax year to look up."),
        state_code: Optional[str] = Query(
            default=None,
            min_length=2,
            max_length=2,
            description="Optional two-letter state abbreviation.",
        ),
    ) -> dict:
        return get_tax_rule_context_dict(tax_year=tax_year, state_code=state_code)

    return app


app = create_app()

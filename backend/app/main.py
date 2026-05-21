from __future__ import annotations

from typing import Optional

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware

from app.config import get_settings
from app.schemas import (
    AgentWarning,
    ChatRequest,
    ChatResponse,
    DocumentExtractionResponse,
    DocumentInput,
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

    @app.post("/api/tax/analyze", response_model=TaxAnalysisResponse)
    def analyze(request: TaxScenarioRequest) -> TaxAnalysisResponse:
        try:
            return analyze_scenario(request)
        except Exception as exc:
            raise HTTPException(
                status_code=500,
                detail="Tax analysis could not be completed safely.",
            ) from exc

    @app.post("/api/chat", response_model=ChatResponse)
    def chat(request: ChatRequest) -> ChatResponse:
        try:
            return generate_chat_reply(request)
        except Exception as exc:
            raise HTTPException(
                status_code=500,
                detail="Chat response could not be generated safely.",
            ) from exc

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

    @app.post("/api/documents/extract", response_model=DocumentExtractionResponse)
    def extract_document(document: DocumentInput) -> DocumentExtractionResponse:
        try:
            return DocumentExtractionResponse(
                status="review_required",
                message=(
                    "Real document extraction is not available yet. The backend received "
                    "the document metadata only and did not extract filing-ready fields."
                ),
                document=document,
                warnings=[
                    AgentWarning(
                        severity="info",
                        code="DOCUMENT_EXTRACTION_NOT_AVAILABLE",
                        message="Document extraction is currently a safe stub.",
                        recommended_follow_up="Ask the user to manually confirm document fields before analysis.",
                    )
                ],
                missing_information=["Confirmed document fields"],
            )
        except Exception as exc:
            raise HTTPException(
                status_code=500,
                detail="Document extraction stub could not process the request safely.",
            ) from exc

    return app


app = create_app()

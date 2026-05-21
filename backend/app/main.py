from __future__ import annotations

import os
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
        live_settings = get_settings()
        openai_key = (os.getenv("OPENAI_API_KEY") or live_settings.openai_api_key or "").strip()
        gemini_key = (os.getenv("GEMINI_API_KEY") or live_settings.gemini_api_key or "").strip()

        if openai_key:
            provider = "openai"
            model = live_settings.openai_model
        else:
            provider = "gemini"
            model = live_settings.gemini_model

        return HealthResponse(
            status="ok",
            service=live_settings.app_name,
            ok=True,
            provider=provider,
            model=model,
            geminiConfigured=bool(gemini_key),
        )

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
            safe_document = DocumentInput(
                document_id=document.document_id,
                document_type=document.document_type,
                file_name=document.file_name,
                extraction_status="needs_review",
                extracted_fields=None,
                notes=None,
            )
            return DocumentExtractionResponse(
                status="review_required",
                message=(
                    "Real document extraction is not available yet. The backend received "
                    "the document metadata only and did not extract filing-ready fields."
                ),
                document=safe_document,
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

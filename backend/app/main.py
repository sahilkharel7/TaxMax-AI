from fastapi import FastAPI, HTTPException
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
from app.services.agent_orchestrator import analyze_tax_scenario


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
    def analyze_tax(request: TaxScenarioRequest) -> TaxAnalysisResponse:
        try:
            return analyze_tax_scenario(request)
        except Exception as exc:
            raise HTTPException(
                status_code=500,
                detail="Tax analysis could not be completed safely.",
            ) from exc

    @app.post("/api/chat", response_model=ChatResponse)
    def chat(request: ChatRequest) -> ChatResponse:
        try:
            if request.scenario is None:
                return ChatResponse(
                    status="needs_more_information",
                    answer=(
                        "I can help with tax preparation review, but I need scenario "
                        "details before giving context-specific guidance."
                    ),
                    next_questions=[
                        "Please provide the tax year, filing status, resident state, and any income or document details you want reviewed."
                    ],
                    missing_information=["Tax scenario"],
                )

            analysis = analyze_tax_scenario(request.scenario)
            return ChatResponse(
                status=analysis.status,
                answer=(
                    "I reviewed the current scenario using deterministic TaxMax AI "
                    "checks. The response is preliminary and requires confirmation "
                    "before any filing decisions."
                ),
                next_questions=analysis.next_questions,
                warnings=analysis.warnings,
                missing_information=analysis.missing_information,
            )
        except Exception as exc:
            raise HTTPException(
                status_code=500,
                detail="Chat response could not be generated safely.",
            ) from exc

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

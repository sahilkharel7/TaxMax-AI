# TaxMax AI

> A minimal, premium, AI-assisted tax preparation prototype for U.S. federal
> returns. Built for design + product demos — not for actual filing.

TaxMax AI walks a user through a clean, guided tax prep flow: upload a W-2 or
1098-T, review the extracted fields, answer a few profile questions, and see an
estimated summary plus legal tax-saving review opportunities — with a
contextual chatbot sidebar available the whole way. A FastAPI backend
(`backend/`) provides chat, scenario analysis, savings optimization, document
extraction validation, and tax-rule lookup endpoints; the frontend talks to it
through a Vite proxy in development.

> **Prototype only.** Document parsing is mocked, summary numbers are
> illustrative, savings opportunities are review prompts rather than final tax
> advice, and there is no e-filing.

## Stack

**Frontend**

- React 19 + TypeScript
- Vite (with `/api` dev proxy → backend on port 8000)
- Tailwind CSS v4

**Backend**

- FastAPI + Pydantic v2
- Uvicorn
- Pytest

## Getting started

You can run the frontend on its own (it falls back to a mock chat reply when
the backend is unreachable), or run the full stack.

### 1. Frontend

```bash
npm install
npm run dev
```

Open http://localhost:5173.

### 2. Backend

```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

Health check: <http://127.0.0.1:8000/api/health>

When the backend is running, the header shows **API connected** and the
chatbot, summary, and final review screens use real backend responses.

#### Environment

Copy `backend/.env.example` to `backend/.env` if you need to override
defaults:

```
GEMINI_API_KEY=your-gemini-api-key
GEMINI_MODEL=gemini-1.5-flash
```

To switch the frontend between mock mode and backend mode, set
`VITE_USE_BACKEND=true`. To point the frontend at a different backend host
(e.g. a deployed instance), set `VITE_API_BASE_URL` before running
`npm run dev`. If you use the Vite dev proxy, `VITE_API_BASE_URL` can stay
unset.

### Other scripts

```bash
# Frontend
npm run build      # type-check + production build
npm run preview    # serve the production build locally
npm run lint       # ESLint

# Backend
pytest -q          # run backend tests (from backend/ with venv active)
```

## API surface

| Method | Path | Purpose |
| ------ | ---- | ------- |
| GET | `/api/health` | Service health check |
| POST | `/api/chat` | Chatbot reply with optional scenario context |
| POST | `/api/tax/analyze` | Structured agent-style review of a tax scenario |
| POST | `/api/tax/optimize` | Structured legal tax-saving opportunity review |
| GET | `/api/tax/rules?tax_year=YYYY&state_code=XX` | Federal + optional state rule context |
| POST | `/api/documents/extract` | Validates upload metadata and returns mocked extraction output |

Schemas are defined in `backend/app/schemas.py` and mirrored in
`src/lib/apiTypes.ts`.

## Backend capability statement

The backend supports a savings-focused review workflow for deductions, credits,
filing status, state context, documentation gaps, and professional-review
checklists. It uses deterministic agents by default and includes a shared
Gemini structured-output contract for safe future agent calls when
`GEMINI_API_KEY` is configured. The app must not be presented as calculating a
final refund, guaranteeing savings, filing a return, or giving tax/legal advice.

## Deployment mode

`vercel.json` currently deploys the Vite frontend as a static app from `dist`.
That mode does not deploy the FastAPI backend. To use backend-supported
analysis, optimization, and chat in production, deploy the backend separately
and set:

```
VITE_USE_BACKEND=true
VITE_API_BASE_URL=https://your-backend.example.com/api
```

Keep `GEMINI_API_KEY` only in the backend environment. Do not expose provider
keys through Vite variables or frontend code.

## App structure

```
src/
  App.tsx                 # Step state machine + layout
  main.tsx                # React root
  index.css               # Tailwind v4 + theme tokens
  types.ts                # Shared TypeScript types
  data/
    mockData.ts           # Mock document data + offline chatbot fallback
  hooks/
    useBackendHealth.ts   # Polls /api/health for the header status pill
    useTaxAnalysis.ts     # Calls /api/tax/analyze with scenario state
    useTaxOptimization.ts # Calls /api/tax/optimize with scenario state
  lib/
    api.ts                # Typed fetch wrappers + ApiError
    apiTypes.ts           # Wire-format types matching backend Pydantic schemas
    scenarioMapping.ts    # Maps UI state to TaxScenarioRequest payloads
  components/
    Header.tsx
    Stepper.tsx
    ChatbotSidebar.tsx    # Calls /api/chat, falls back to mock on failure
    ui/                   # Reusable primitives (Button, Card, Input, ...)
  screens/
    Welcome.tsx
    Upload.tsx
    ManualEntry.tsx
    ParsedReview.tsx
    TaxProfile.tsx
    Summary.tsx           # Renders backend findings + warnings + missing info
    FinalReview.tsx       # Combines local + backend warnings

backend/
  app/
    main.py               # FastAPI app + routes
    config.py             # Settings (env-driven)
    schemas.py            # Pydantic request/response models
    services/
      chat_service.py     # Deterministic chat replies (placeholder)
      analysis_service.py # Deterministic scenario analysis (placeholder)
      gemini_agent_contracts.py # Shared structured-output contract for agents
      tax_rule_service.py # Loads federal/state JSON rule files
      tax_optimization_service.py # Savings-opportunity review workflow
    tax_rules/
      federal/2025.json
      states/CA/2025.json
      states/NY/2025.json
  tests/                  # pytest suite
```

## User flow

1. **Welcome** — choose document upload or manual entry
2. **Documents** *(upload path)* — drag-and-drop W-2 / 1098-T / 1099-INT, mock parsing
3. **Manual entry** *(manual path)* — personal info, filing status, income, education, credits
4. **Parsed review** — confirm each extracted field with edit + confirm
5. **Tax profile** — filing status and yes/no questions
6. **Summary** — estimated refund / amount owed, agent insights, and savings opportunities
7. **Final review** — section-by-section status + local and backend warnings, prepare review package

A **TaxMax Guide** chatbot sidebar is available throughout the flow. It posts
each user message (with the current scenario context) to `/api/chat` and
displays the structured response. If the backend is unreachable, it falls back
to the local mock replies and shows a small offline notice.

## Design principles

- White / black / gray with a subtle blue accent
- Generous white space, large readable type, soft borders and shadows
- One clear primary action per screen
- Step-based flow with a persistent stepper
- Trust indicators visible in the header
- Plain-language copy throughout

## Disclaimers (also visible in the UI)

- TaxMax AI provides AI-assisted preparation support. It does not provide legal
  or tax advice.
- Document parsing may contain errors. Always review and confirm your
  information.
- E-filing is not available in this prototype.
- Savings opportunities are prompts for review and documentation, not final
  eligibility decisions or guaranteed tax outcomes.

## License

Private prototype. All rights reserved.

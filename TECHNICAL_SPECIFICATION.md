# TaxMax AI MVP Technical Specification

## 1. Purpose

TaxMax AI is a U.S.-based AI-assisted tax preparation and review product. The MVP should begin as a polished frontend prototype that feels like a real product demo, then evolve into a FastAPI and Gemini-powered tax agent platform.

The current frontend prompt defines Phase 1 as a frontend-only prototype. That means Phase 1 must not perform real IRS filing, real tax calculations, real document parsing, or real API calls. It should use mock data and placeholder logic while making the user experience feel complete, premium, calm, and trustworthy.

The future backend phase will use FastAPI, Gemini API keys, and agent workflows to analyze federal and state tax assumptions, deductions, credits, documentation needs, and legal optimization opportunities.

## 2. Product Name and Positioning

- Product name: TaxMax AI
- Country: United States
- Product type: AI-assisted tax preparation and review app
- Design tone: minimal, premium, calm, professional, trustworthy
- Design inspiration: Apple, Tesla, modern fintech apps, and a simplified TurboTax-style guided flow
- Primary MVP audience: users preparing simple U.S. tax returns with documents such as W-2, 1098-T, 1099-INT, and related tax forms

## 3. MVP Phasing

### Phase 1: Frontend Prototype

Phase 1 is the immediate implementation target from `frontend_prompt.md`.

Requirements:

- React with TypeScript and TSX.
- Tailwind CSS.
- Frontend-only implementation.
- No real backend.
- No real Gemini calls.
- No real IRS filing.
- No real tax calculations.
- No real document parsing.
- Mock parser behavior.
- Mock chatbot responses.
- Mock tax summary values.
- Investor, user, or hackathon-ready product demo.

### Phase 2: Backend MVP

Phase 2 adds a real backend after the frontend prototype is complete.

Requirements:

- FastAPI backend.
- Gemini API keys stored server-side.
- Agent orchestration for tax analysis.
- Federal and state tax rule datasets.
- Structured backend responses.
- Real API integration only from backend services.

### Phase 3: Production Platform

Phase 3 adds persistence, authentication, PDF extraction, audit logging, and deployment hardening.

Requirements:

- PostgreSQL.
- Private document storage.
- User authentication.
- Authorization checks.
- Audit logs.
- Rate limiting.
- Monitoring.
- Security review.

## 4. Phase 1 Frontend Stack

- Framework: React
- Language: TypeScript / TSX
- Build tool: Vite
- Styling: Tailwind CSS
- State: React state
- API calls: none in Phase 1
- Data: mock data only
- Chatbot: mocked contextual responses

The code should stay simple, modular, and easy to connect to a backend later.

## 5. Phase 1 Frontend Architecture

```text
+-----------------------------+
| Browser                     |
| React + TypeScript + Vite   |
+--------------+--------------+
               |
               v
+--------------+--------------+
| App Shell                   |
| - Header                    |
| - Progress stepper          |
| - Main workflow area        |
| - Chatbot sidebar           |
+--------------+--------------+
               |
               v
+--------------+--------------+
| Local React State           |
| - Current step              |
| - Uploaded mock documents   |
| - Manual entry fields       |
| - Confirmed parsed fields   |
| - Tax profile answers       |
| - Mock summary              |
| - Chat messages             |
+-----------------------------+
```

No Phase 1 component should require a server to work.

## 6. Phase 1 User Workflow

```text
Welcome
  |
  +--> Start with document upload
  |       |
  |       v
  |    Upload documents
  |       |
  |       v
  |    Mock parsing state
  |       |
  |       v
  |    Parsed document review
  |
  +--> Enter manually
          |
          v
       Manual entry form

Parsed review or manual entry
  |
  v
Tax profile questions
  |
  v
Summary dashboard
  |
  v
Final review
  |
  v
Prepare review package
```

The chatbot sidebar remains available through the workflow and provides contextual explanations based on the active step.

## 7. Phase 1 Screens

### 7.1 Welcome Screen

Headline:

```text
File smarter with TaxMax AI
```

Subtext:

```text
Upload your tax documents or enter your information manually. TaxMax AI helps organize, review, and explain your return.
```

Primary actions:

- Start with document upload
- Enter manually

Purpose:

Introduce the product clearly and route the user into the guided flow.

### 7.2 Document Upload Screen

Supported mock document types:

- W-2
- 1098-T
- 1099-INT
- Other tax document

UI requirements:

- Drag-and-drop upload area.
- Accepted file types label: PDF, JPG, PNG.
- Mock upload behavior.
- Mock "Parsing document..." state.
- Uploaded document list.
- Delete document option.
- Trust indicators:
  - Encrypted upload
  - You control your documents
  - Review before submission
  - Delete uploaded files anytime

### 7.3 Manual Entry Screen

Forms:

- Personal information.
- Filing status.
- W-2 income.
- Federal withholding.
- Education expenses.
- Student status.
- Basic credits checklist.

The form should use plain language and avoid tax jargon where possible.

### 7.4 Parsed Document Review Screen

The user must confirm extracted mock fields before moving forward.

Example W-2 fields:

- Employer name.
- Employer EIN.
- Wages, tips, and compensation.
- Federal income tax withheld.
- Social Security wages.
- Medicare wages.

Each parsed field card should include:

- Label.
- Extracted value.
- Source reference, such as "W-2 Box 1".
- Edit button.
- Confirm checkbox or status.

### 7.5 Tax Profile Screen

Guided questions:

- Are you filing as Single, Married Filing Jointly, Married Filing Separately, Head of Household, or Qualifying Surviving Spouse?
- Can someone else claim you as a dependent?
- Were you a student this year?
- Did you receive a 1098-T?
- Did you have more than one job?
- Did you receive any 1099 forms?

Use clean selectable cards, segmented controls, or yes/no choices.

### 7.6 Summary Dashboard

Show a mock tax summary:

- Total income.
- Federal tax withheld.
- Estimated taxable income.
- Possible education credit review.
- Estimated refund or amount owed.

Required label:

```text
Estimate only. Final results require full review.
```

### 7.7 Final Review Screen

Sections:

- Personal Info.
- Income.
- Education.
- Credits.
- Documents.
- Review warnings.

Status indicators:

- Complete.
- Needs review.
- Missing information.

Final action:

```text
Prepare review package
```

Do not include a real "File with IRS" button.

Instead show:

```text
E-filing integration coming soon
```

## 8. Chatbot Sidebar

The chatbot sidebar is called:

```text
TaxMax Guide
```

It should be persistent throughout the app and should not block the main workflow.

### 8.1 Chatbot Features

- Welcome message.
- Suggested prompts.
- Input box.
- Mock responses.
- Contextual help based on the current step.
- Small professional disclaimer.

Required disclaimer:

```text
I can explain tax terms and guide you through the app, but I do not replace a qualified tax professional.
```

### 8.2 Suggested Prompts

- What is a W-2?
- Where do I find Box 1?
- Do I need a 1098-T?
- Can someone claim me as a dependent?
- Why do I need to review extracted data?
- What documents should I upload?

### 8.3 Chatbot Response Rules

The chatbot should guide and explain. It should not make final tax decisions.

Avoid:

```text
You qualify for this credit.
```

Use:

```text
Based on your answers, you may be eligible. Please review the requirement checklist.
```

## 9. Phase 1 Component Plan

Recommended source structure:

```text
src/
  App.tsx
  main.tsx
  components/
    AppShell.tsx
    Header.tsx
    ProgressStepper.tsx
    WelcomeScreen.tsx
    UploadCard.tsx
    ManualEntryForm.tsx
    ParsedDocumentReview.tsx
    TaxProfileQuestions.tsx
    SummaryDashboard.tsx
    FinalReviewChecklist.tsx
    ChatbotSidebar.tsx
    Button.tsx
    Input.tsx
    Card.tsx
    StatusBadge.tsx
  data/
    mockTaxData.ts
  types/
    tax.ts
  styles/
    index.css
```

Component diagram:

```text
App
 |
 +-- AppShell
     |
     +-- Header
     +-- ProgressStepper
     +-- MainStepRenderer
     |   |
     |   +-- WelcomeScreen
     |   +-- UploadCard
     |   +-- ManualEntryForm
     |   +-- ParsedDocumentReview
     |   +-- TaxProfileQuestions
     |   +-- SummaryDashboard
     |   +-- FinalReviewChecklist
     |
     +-- ChatbotSidebar
```

## 10. Mock Data Requirements

### 10.1 W-2 Mock Data

```text
Employer: Acme Technologies Inc.
EIN: 12-3456789
Wages: $42,350.00
Federal tax withheld: $4,280.00
Social Security wages: $42,350.00
Medicare wages: $42,350.00
```

### 10.2 1098-T Mock Data

```text
School: Columbia University
Tuition payments: $18,500.00
Scholarships/grants: $7,500.00
```

### 10.3 Mock Parser Flow

```text
User drops file
  |
  v
Add file to upload list
  |
  v
Show "Parsing document..."
  |
  v
Wait briefly with mock loading state
  |
  v
Return mock W-2 or 1098-T values
  |
  v
Require user review and confirmation
```

## 11. UX and Visual Requirements

The frontend should feel calm and premium.

Requirements:

- Minimal white, black, and gray palette.
- Subtle blue accent.
- Generous whitespace.
- Large readable typography.
- Clean cards with soft borders.
- Rounded corners.
- Subtle shadows.
- Minimal buttons.
- Smooth transitions where useful.
- Responsive layout.
- One clear main action per screen.
- Step indicator always visible.
- Chatbot sidebar visible but secondary.

Layout:

```text
+----------------------------------------------------------+
| Header                                                   |
+----------------------------------------------------------+
| Progress Stepper                                         |
+---------------------------------------+------------------+
| Main workflow content                | TaxMax Guide      |
|                                      | Chatbot sidebar   |
|                                      |                  |
+---------------------------------------+------------------+
```

Responsive behavior:

```text
Desktop:
  Main content left or center, chatbot on right.

Tablet:
  Main content full width, chatbot collapsible or below.

Mobile:
  Step content first, chatbot accessible through drawer or bottom panel.
```

## 12. Privacy and Trust UI

Visible trust indicators:

- Encrypted upload.
- You control your documents.
- Review before submission.
- Delete uploaded files anytime.

Required disclaimers:

```text
TaxMax AI provides AI-assisted preparation support. It does not provide legal or tax advice.
```

```text
Document parsing may contain errors. Always review and confirm your information.
```

```text
E-filing is not available in this prototype.
```

## 13. Phase 1 Acceptance Criteria

The frontend prototype is complete when:

- The app is built in React TypeScript with TSX.
- Tailwind CSS is used for styling.
- The app runs without backend dependencies.
- All seven screens are connected in a guided flow.
- Upload flow uses mock parsing behavior.
- Manual entry path is available.
- Parsed review requires confirmation before continuing.
- Tax profile questions are selectable.
- Summary dashboard shows mock estimate values.
- Final review shows section statuses.
- Chatbot sidebar is persistent and contextual.
- Privacy and tax disclaimers are visible.
- No real IRS filing action exists.
- No real tax calculations or legal claims are made.
- Code is modular and ready for backend connection later.

## 14. Phase 2 FastAPI Backend Architecture

After Phase 1, the backend should be implemented with FastAPI.

```text
React TSX Frontend
  |
  | JSON API requests
  v
FastAPI Backend
  |
  +--> Pydantic validation
  +--> Agent orchestration
  +--> Tax rule lookup
  +--> Gemini client
  |
  v
Structured response to frontend
```

Recommended backend structure:

```text
backend/
  app/
    main.py
    config.py
    schemas.py
    services/
      gemini_client.py
      agent_orchestrator.py
      tax_rule_service.py
      document_service.py
    agents/
      federal_tax_agent.py
      state_tax_agent.py
      deduction_agent.py
      credit_agent.py
      optimization_agent.py
      risk_review_agent.py
      summary_agent.py
  tests/
    test_health.py
    test_agent_orchestrator.py
    test_payload_validation.py
```

Environment:

```text
GEMINI_API_KEY=your-gemini-api-key
GEMINI_MODEL=gemini-2.5-pro
```

The Gemini API key must remain server-side.

## 15. Phase 2 Agent System

The future backend should calculate and reason through tax assumptions using specialized agents, not frontend hardcoding.

Agent workflow:

```text
Tax scenario request
  |
  v
Agent Orchestrator
  |
  +--> Federal Tax Agent
  +--> State Tax Agent
  +--> Deduction Agent
  +--> Credit Agent
  +--> Optimization Agent
  +--> Risk Review Agent
  +--> Summary Agent
  |
  v
Validated structured response
```

Agent responsibilities:

- Federal Tax Agent: federal income assumptions, filing status, bracket exposure, federal deduction and credit context.
- State Tax Agent: resident state, work state, local tax, state-specific deductions and credits.
- Deduction Agent: IRA, HSA, education-related, home office, and other applicable deductions based on eligibility.
- Credit Agent: education credits, clean energy credits, dependent-related credits, and state-specific credits.
- Optimization Agent: compares legal planning scenarios and ranks possible benefits.
- Risk Review Agent: identifies documentation needs, uncertainty, and audit-risk level.
- Summary Agent: converts technical findings into plain-language user guidance.

## 16. Phase 2 API Design

### 16.1 Health

```http
GET /api/health
```

Response:

```json
{
  "ok": true,
  "provider": "gemini",
  "model": "gemini-2.5-pro",
  "geminiConfigured": true
}
```

### 16.2 Analyze Tax Scenario

```http
POST /api/tax/analyze
```

Purpose:

Runs the full federal, state, deduction, credit, optimization, and risk agent workflow.

### 16.3 Chat

```http
POST /api/chat
```

Purpose:

Routes user questions to the correct Gemini-backed agent workflow.

### 16.4 Extract Tax Document

```http
POST /api/documents/extract
```

Purpose:

Future endpoint for real W-2, 1098-T, and other document extraction. This is not part of the Phase 1 frontend-only prototype.

## 17. Federal and State Tax Rule Plan

Future tax assumptions should be versioned by tax year and jurisdiction.

Recommended structure:

```text
backend/app/tax_rules/
  federal/
    2025.json
    2026.json
  states/
    NY/
      2025.json
      2026.json
    CA/
      2025.json
      2026.json
```

Rule lookup workflow:

```text
Read user tax year
  |
  v
Load federal rule file
  |
  v
Load resident state rule file
  |
  v
If work state differs, load work state rule file
  |
  v
If locality applies, load local assumptions
  |
  v
Pass rule context to agents
```

Every rule file should include:

- Tax year.
- Jurisdiction.
- Filing statuses.
- Brackets.
- Standard deductions.
- Common deductions.
- Common credits.
- Source references.
- Last reviewed date.

## 18. Data Persistence Plan

Phase 1 has no database.

Future production should use:

- PostgreSQL for users, sessions, W-2 records, agent runs, and chat messages.
- Private object storage for uploaded documents.
- Encryption at rest for sensitive data.
- Audit logs for agent outputs and user confirmations.

Future persistence architecture:

```text
FastAPI
  |
  +--> PostgreSQL
  |     - users
  |     - tax_sessions
  |     - w2_records
  |     - agent_runs
  |     - chat_messages
  |
  +--> Object Storage
        - uploaded PDFs
        - extracted document artifacts
```

## 19. Security Requirements

Phase 1:

- No real API keys in frontend.
- No real document upload to server.
- No real tax filing.
- User-facing disclaimers must be visible.

Phase 2 and beyond:

- Store `GEMINI_API_KEY` only in backend environment variables.
- Never expose provider keys to React.
- Validate all uploaded files.
- Limit upload size.
- Avoid logging full tax payloads.
- Add authentication before storing sessions.
- Add authorization before loading saved data.
- Add rate limiting to AI endpoints.
- Use HTTPS in deployment.

## 20. Testing Plan

### 20.1 Frontend Prototype Tests

- App renders without errors.
- User can start with document upload.
- User can enter manually.
- Upload flow shows mock parsing state.
- Parsed fields can be confirmed.
- User cannot continue from parsed review until required fields are confirmed.
- Tax profile questions update state.
- Summary dashboard shows mock values.
- Final review displays complete, needs review, and missing statuses.
- Chatbot suggested prompts produce mock responses.
- Responsive layout works on desktop, tablet, and mobile.

### 20.2 Future Backend Tests

- `GET /api/health` returns Gemini configuration status.
- `POST /api/tax/analyze` validates payloads.
- Agent orchestrator returns required structured fields.
- Missing Gemini key returns a clear error.
- Tax rule lookup loads the correct federal and state assumptions.
- Document extraction rejects unsupported file types.

## 21. Local Development Commands

Frontend Phase 1:

```bash
npm install
npm run dev
```

Future backend:

```bash
cd backend
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

## 22. Cleanup Requirements

After rebuilding the frontend from the prompt:

- Remove old mirrored `assets/`.
- Remove unrelated demo code.
- Remove generated `dist/` from git tracking.
- Keep only TaxMax AI source files.
- Keep frontend code as React TSX, not minified JavaScript.

Target root structure:

```text
README.md
TECHNICAL_SPECIFICATION.md
frontend_prompt.md
index.html
package.json
package-lock.json
vite.config.ts
tailwind.config.ts
postcss.config.js
src/
backend/
```

## 23. Final MVP Acceptance Criteria

The MVP is acceptable when:

- It matches the `frontend_prompt.md` product flow.
- It uses React TypeScript and Tailwind CSS.
- It is frontend-only for Phase 1.
- It includes all required screens.
- It includes the persistent TaxMax Guide chatbot.
- It uses mock document parsing and mock tax summaries.
- It includes all required disclaimers.
- It feels premium, clean, and trustworthy.
- It is structured so a FastAPI and Gemini backend can be connected in Phase 2.

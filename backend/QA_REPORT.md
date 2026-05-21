# TaxMax AI Backend — QA Report

**Scope:** FastAPI MVP at `backend/app/`, agents at `backend/app/agents/`,
services at `backend/app/services/`, rule data at `backend/app/tax_rules/`,
tests at `backend/tests/`.

**Test command:** `python -m pytest -q` (from `backend/` with `.venv` active).

**Final result:** **89 passed, 0 failed** (2 deprecation warnings from
`google-genai`, both upstream).

---

## 1. What passed (verified by tests)

### Routes

- `GET /api/health` returns `200` with `{status, service, ok, provider,
  model, geminiConfigured}` in both Gemini-configured and Gemini-missing
  states. Raw key never present in body or headers.
- `POST /api/tax/analyze` returns `200` with a `TaxAnalysisResponse` shape
  (`status`, `findings`, `warnings`, `next_questions`, `missing_information`,
  `disclaimer`) for valid payloads.
- `POST /api/chat` returns `200` for valid messages and `422` for empty /
  oversized / non-string messages.
- `POST /api/documents/extract` returns a controlled "not available yet"
  stub for supported `document_type`s and `422` for unsupported / missing
  types.
- `GET /api/tax/rules` loads federal 2025 and CA/NY 2025 rules, returns a
  controlled `TaxRuleError` for missing year / unknown state.

### Agent orchestration

- All seven agents run in the spec-mandated order:
  `FederalTaxAgent → StateTaxAgent → DeductionAgent → CreditAgent →
  OptimizationAgent → RiskReviewAgent → SummaryAgent`. Asserted in
  `tests/test_tax_analyze_endpoint.py::test_analyze_runs_full_agent_lineup_in_specified_order`.
- Warnings and `next_questions` are deduplicated across agents.
- Findings are structured `AgentFinding` objects, not free-form Gemini text.
- Critical product signals are surfaced:
  - `can_be_claimed_as_dependent == None` → `MISSING_DEPENDENCY_CONTEXT`
    / `MISSING_DEPENDENT_STATUS` warning + "Dependency status" missing.
  - `received_1098_t == True` → `Credit Agent` finding "Education credit
    review may apply".
  - Document with `extraction_status == "needs_review"` → review finding +
    `DOCUMENT_EXTRACTION_NEEDS_REVIEW` warning.
  - Missing rule file (e.g. `tax_year=2024`) → controlled
    `TAX_RULE_FILE_MISSING` warning, no crash, no invented tax law.

### Gemini safety (no live model calls)

- Missing `GEMINI_API_KEY` raises `GeminiNotConfiguredError`, which the
  summary agent catches and falls back to deterministic output. No 5xx.
- `httpx.TimeoutException` from Gemini → controlled fallback dict
  (`status: "fallback"`, `retryable: True`).
- Invalid JSON or non-JSON Gemini text → controlled fallback dict
  (`retryable: False`). No raw model text leaks into the API response.
- `tests/test_summary_agent_gemini.py` verifies that the payload sent to
  Gemini contains *presence flags only* (`w2_wages: True`), never the raw
  amounts.

### Cautious tax/legal language

- The spec-driven analyze test scans the full response and asserts none of
  the banned phrases appear:
  - `you qualify`, `you definitely qualify`, `you will qualify`,
    `guaranteed refund`, `guaranteed to receive`, `you will receive`,
    `you are entitled to`, `100% refund`.
- Cautious phrases (`may apply`, `needs review`, `requires confirmation`,
  `should be reviewed`) are required to appear at least once.
- Regex check rejects fabricated dollar refund / tax-due claims
  (`refund of \$`, `you will get \$`, `tax due of \$`, `you owe \$`).
- Chat refuses adversarial prompts:
  - "Can you file my taxes with the IRS?" → "TaxMax AI cannot file your
    return with the IRS … E-filing is not available in this prototype."
  - "Tell me exactly how much refund I will get." → "I can't confirm an
    exact refund amount or final eligibility…"
  - "Do I qualify for the education credit?" → uses cautious wording, no
    final eligibility claim.
- All chat responses include the standard disclaimer.

### Security contract

- Sentinel `GEMINI-KEY-SENTINEL-9aF1c3` set as `GEMINI_API_KEY` env var
  never appears in `/api/health`, `/api/tax/analyze`, `/api/chat`, or
  `/api/documents/extract` responses (body or headers).
- Validation errors return JSON `detail` only — no Python tracebacks,
  filesystem paths, or `site-packages` strings in `422` or `404`
  responses.

---

## 2. What failed during the audit (now fixed)

| # | Issue                                                                                                                                                            | Fix                                                                                                                                                                          | Files                                                          |
| - | ---------------------------------------------------------------------------------------------------------------------------------------------------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | -------------------------------------------------------------- |
| 1 | `/api/health` only exposed `{status, service}`. Spec required `ok`, `provider`, `model`, `geminiConfigured` so the frontend / ops can detect missing keys.       | Extended `HealthResponse` with `ok`, `provider`, `model`, `gemini_configured` (alias `geminiConfigured`). Endpoint computes `gemini_configured` without echoing the raw key. | `backend/app/schemas.py`, `backend/app/main.py`                |
| 2 | `/api/chat` had no explicit refusal for "Can you file my taxes with the IRS?" or "Tell me exactly how much refund I will get." It fell through to a vague reply. | Added two regex rules at the top of `_REPLY_RULES` that produce explicit refusals citing "E-filing is not available" and "I can't confirm an exact refund amount".           | `backend/app/services/chat_service.py`                         |
| 3 | `ChatRequest.message` had `min_length=1` but no `max_length`, so a 5000-char prompt was accepted.                                                                | Added `max_length=4000` so oversized prompts return `422` before reaching the model.                                                                                         | `backend/app/schemas.py`                                       |
| 4 | `/api/documents/extract` echoed user-supplied `notes` and `extracted_fields` straight back, allowing reflection of arbitrary user content.                       | Endpoint now returns a sanitized `DocumentInput` with `notes=None`, `extracted_fields=None`, and `extraction_status="needs_review"` — only safe metadata is echoed.          | `backend/app/main.py`                                          |
| 5 | A draft refusal phrase contained the literal substring `"you definitely qualify"` (as part of "whether you definitely qualify…"). Tripped the banned-phrase QA.  | Reworded the refusal to avoid the substring entirely while keeping the cautious meaning.                                                                                     | `backend/app/services/chat_service.py`                         |
| 6 | No coverage for: payload validation (negative amounts, invalid state codes, missing profile, oversized goal), document extract endpoint, or security sentinels.  | Added 4 new test files: `test_payload_validation.py`, `test_tax_analyze_endpoint.py`, `test_document_extract_endpoint.py`, `test_security_contract.py`.                      | `backend/tests/`                                               |

---

## 3. What remains risky (not blocking for demo, but track)

1. **Schema vs. spec field-name drift.** The QA spec uses field names that
   do not match the live Pydantic schema:
   - spec `taxpayer_profile` → schema `profile`
   - spec `tax_year` (top-level) → schema `profile.tax_year`
   - spec `federal_tax_withheld` → schema `federal_withholding`
   - spec `social_security_wages`, `medicare_wages` → not in schema
   - spec `documents[].filename` / `confirmed` → schema `file_name` /
     `extraction_status`
   - spec `is_student`, `has_1098_t`, `school_name`, `tuition_payments`,
     `scholarships_grants` → schema `was_student`, `received_1098_t`,
     `institution_name`, `qualified_expenses`, `scholarships_or_grants`

   The live frontend (`src/lib/scenarioMapping.ts`) is already tracking the
   schema names, so I tested against the schema. **Action**: align the
   spec doc with the implementation OR add a translation layer in the API
   to accept both naming conventions. Do not silently map fields — that
   risks dropping data.

2. **`extra="ignore"` on Pydantic models.** Currently unknown top-level
   fields like `unknown_extra_field` are silently dropped. The QA tests
   confirm they are not echoed back, but switching to `extra="forbid"`
   would catch frontend / contract drift sooner. Held back for now to
   avoid breaking in-flight frontend changes.

3. **Tax rule data is placeholder.** Federal/CA/NY 2025 JSON files load,
   but the agents already note that values "are placeholders pending
   verified data; agents must not rely on them for calculations yet."
   No demo issue, but do not let any future agent compute tax against
   these files.

4. **Gemini live path is unverified.** Tests inject fakes for the model
   client; we never call real Gemini. When the key is added in staging,
   re-run `tests/test_gemini_client.py` against a real key once and
   verify the structured response contract end-to-end.

5. **CORS allow-list is hard-coded** to local dev origins
   (`localhost:3000/5173`, `127.0.0.1:3000/5173`). Add the production
   origin (and remove dev origins) before any non-local deploy.

6. **No request-level rate limiting.** Chat and analyze endpoints accept
   unbounded request volume per IP. Acceptable for demo, not for public
   exposure.

7. **`/api/documents/extract` is a stub.** It validates and echoes
   metadata but does not read uploaded file bytes. Real extraction must
   route through a malware-scan, MIME sniff, and size cap before any
   parser runs.

---

## 4. Security concerns (audited, none open)

- API key handling: `gemini_client._gemini_api_key` reads from env first,
  then settings; the value never leaves the process. `generate_structured_agent_response`
  catches all exceptions and replaces them with a static fallback message
  — no upstream stack frame or auth header reaches the client.
- Tax payloads: `_safe_user_content` JSON-serializes only the requested
  payload and three control instructions; no logger writes the prompt,
  payload, or response text.
- Headers: TestClient confirms no response header carries the sentinel
  key.
- 5xx handling: `analyze` and `chat` endpoints wrap their service calls in
  generic `HTTPException(500, "<safe message>")`. No `repr(exc)` or
  traceback is ever returned.

## 5. Tax/legal wording concerns (audited, none open)

- All seven agents use review-language only. Banned phrases (`you
  qualify`, `guaranteed`, `you will receive`, etc.) are blocked by both
  source review and a runtime test that walks the entire JSON response.
- Chat endpoint now refuses: e-filing requests, exact-refund demands, and
  "do I qualify" framing.
- Disclaimer is non-empty on every analyze, chat, and extract response.

## 6. Recommended next steps (priority order)

1. **Reconcile schema vs. product-spec field names** (item 3.1) before
   front-end / back-end drift causes silent data loss.
2. **Add a small structured logging layer** that redacts any field whose
   key contains `key|secret|wage|withholding|ssn|tin` so production logs
   stay clean even after Gemini integration lands.
3. **Wire real Gemini calls** in a staging environment, then add a
   contract test that pins the JSON shape Gemini actually returns for
   each agent prompt. The current fallback covers the safe path; we need
   one happy-path live test.
4. **Add per-IP rate limiting** (e.g. `slowapi`) for `/api/chat` and
   `/api/tax/analyze` before exposing the backend beyond local demo.
5. **Replace the document-extract stub** with a real pipeline: file
   upload (`multipart/form-data`) → size + MIME validation → background
   parse → store extraction with `extraction_status` set conservatively.
   Until then, keep the stub's sanitizing behavior added in this PR.
6. **Promote the agent registry** out of a module-level list so failing
   agents can be skipped instead of crashing the orchestrator. Today,
   any agent raising would surface as a generic 500. The spec calls for
   "Handles one failing agent without crashing the whole API, if
   designed that way" — current design does NOT have this; deliberately
   left as-is and called out here.
7. **Tighten `extra="forbid"`** on `TaxScenarioRequest` and friends once
   the frontend is confirmed to send no stray fields.

---

## 7. Files changed by this audit

| File                                               | Change                                                                |
| -------------------------------------------------- | --------------------------------------------------------------------- |
| `backend/app/main.py`                              | Health endpoint returns new fields; document-extract sanitizes echo.  |
| `backend/app/schemas.py`                           | `HealthResponse` extended; `ChatRequest.message` capped at 4000 chars.|
| `backend/app/services/chat_service.py`             | Two new refusal rules (e-filing, exact refund / definite qualify).    |
| `backend/tests/test_health.py`                     | Rewritten with key-presence and key-leak coverage.                    |
| `backend/tests/test_chat_endpoint.py`              | Rewritten with refusal + banned-phrase coverage.                      |
| `backend/tests/test_payload_validation.py`         | **New.** Pydantic 422 + traceback-leak audit.                         |
| `backend/tests/test_tax_analyze_endpoint.py`       | **New.** Spec-driven scenario, agent order, cautious-wording audit.   |
| `backend/tests/test_document_extract_endpoint.py`  | **New.** Stub contract + reflection / leak audit.                     |
| `backend/tests/test_security_contract.py`          | **New.** API key sentinel, missing-key resilience, refusal sentinels. |
| `backend/SMOKE_TESTS.md`                           | **New.** Manual curl + pytest commands.                               |
| `backend/QA_REPORT.md`                             | **New.** This report.                                                 |

## 8. Reproduce locally

```bash
cd backend
python3 -m venv .venv                    # first time only
source .venv/bin/activate
pip install -r requirements.txt          # first time only
python -m pytest -q                      # 89 passed
uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
# in another shell:
curl -s http://127.0.0.1:8000/api/health
```

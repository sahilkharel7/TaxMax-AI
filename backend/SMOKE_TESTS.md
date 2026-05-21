# Backend smoke tests

Manual smoke commands for the TaxMax AI FastAPI backend (`backend/app/main.py`).
Use these after a deploy or large refactor to confirm the four core endpoints
are healthy before exercising the full automated suite.

## 1. Start the backend

```bash
cd backend
python3 -m venv .venv                     # first time only
source .venv/bin/activate
pip install -r requirements.txt           # first time only
uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
```

Optional environment overrides (place in `backend/.env` or export in shell):

```bash
export GEMINI_API_KEY=your-key            # leave unset for offline / fallback mode
export GEMINI_MODEL=gemini-1.5-flash
```

## 2. Run the test suite

From `backend/` with the venv active:

```bash
python -m pytest -q
```

Expected: **89 passed, 0 failed** (warnings from `google-genai` deprecations
are upstream and harmless).

## 3. /api/health

```bash
curl -s http://127.0.0.1:8000/api/health | python3 -m json.tool
```

Expected (Gemini key not set):

```json
{
    "status": "ok",
    "service": "TaxMax AI API",
    "ok": true,
    "provider": "gemini",
    "model": "gemini-1.5-flash",
    "geminiConfigured": false
}
```

With `GEMINI_API_KEY` set, `geminiConfigured` flips to `true`. The raw key is
never returned.

## 4. /api/tax/analyze

Spec scenario (NY student, unknown dependency status, 1098-T present, one
unconfirmed document):

```bash
curl -s -X POST http://127.0.0.1:8000/api/tax/analyze \
  -H "Content-Type: application/json" \
  -d '{
    "profile": {
      "filing_status": "single",
      "tax_year": 2025,
      "resident_state": "NY",
      "work_state": "NY",
      "can_be_claimed_as_dependent": null,
      "was_student": true,
      "received_1098_t": true,
      "multiple_jobs": false,
      "received_1099": false
    },
    "income": {
      "w2_wages": "42350.00",
      "federal_withholding": "4280.00",
      "interest_income": "120.00"
    },
    "education": {
      "is_student": true,
      "received_1098_t": true,
      "qualified_expenses": "18500.00",
      "scholarships_or_grants": "7500.00",
      "institution_name": "Columbia University"
    },
    "documents": [
      {"document_id":"doc_w2_001","document_type":"w2","file_name":"sample-w2.pdf","extraction_status":"parsed"},
      {"document_id":"doc_1098t_001","document_type":"1098_t","file_name":"sample-1098t.pdf","extraction_status":"needs_review"}
    ],
    "user_goal": "Help me review my W-2 and 1098-T before I file."
  }' | python3 -m json.tool | head -60
```

Expected (high level):

- HTTP **200**.
- `status` is `"needs_more_information"` or `"review_required"`.
- `findings[]` contains entries from `Federal Tax Agent`, `State Tax Agent`,
  `Credit Agent` (with summary like "Education credit review may apply ...").
- `warnings[]` includes a `MISSING_DEPENDENCY_CONTEXT` (or
  `MISSING_DEPENDENT_STATUS`) and a `DOCUMENT_EXTRACTION_NEEDS_REVIEW`.
- `missing_information` includes `"Dependency status"`.
- `disclaimer` is non-empty.
- No `"you qualify"`, `"guaranteed refund"`, or fabricated dollar refund.

Failure example (invalid filing status):

```bash
curl -s -o /dev/null -w "%{http_code}\n" -X POST http://127.0.0.1:8000/api/tax/analyze \
  -H "Content-Type: application/json" \
  -d '{"profile": {"filing_status": "married-with-cats", "tax_year": 2025, "resident_state": "NY"}}'
# Expected: 422
```

## 5. /api/chat

Educational topic:

```bash
curl -s -X POST http://127.0.0.1:8000/api/chat \
  -H "Content-Type: application/json" \
  -d '{"message":"What is a W-2?"}' | python3 -m json.tool
```

Adversarial prompts (must refuse, never claim eligibility / refund):

```bash
curl -s -X POST http://127.0.0.1:8000/api/chat \
  -H "Content-Type: application/json" \
  -d '{"message":"Can you file my taxes with the IRS?"}' | python3 -m json.tool
# answer should contain "cannot file" / "E-filing is not available"

curl -s -X POST http://127.0.0.1:8000/api/chat \
  -H "Content-Type: application/json" \
  -d '{"message":"Tell me exactly how much refund I will get."}' | python3 -m json.tool
# answer should refuse exact refund amount

curl -s -X POST http://127.0.0.1:8000/api/chat \
  -H "Content-Type: application/json" \
  -d '{"message":"Do I qualify for the education credit?"}' | python3 -m json.tool
# answer must NOT contain "you qualify" / "guaranteed"
```

Failure example (empty message):

```bash
curl -s -o /dev/null -w "%{http_code}\n" -X POST http://127.0.0.1:8000/api/chat \
  -H "Content-Type: application/json" \
  -d '{"message":""}'
# Expected: 422
```

## 6. /api/documents/extract

Safe-stub call (W-2 metadata):

```bash
curl -s -X POST http://127.0.0.1:8000/api/documents/extract \
  -H "Content-Type: application/json" \
  -d '{"document_type":"w2","file_name":"sample-w2.pdf"}' | python3 -m json.tool
```

Expected:

- HTTP **200**, `status: "review_required"`.
- `message` says extraction is not available.
- `warnings[0].code == "DOCUMENT_EXTRACTION_NOT_AVAILABLE"`.
- `disclaimer` warns the response is not filing-ready.
- The echoed `document` is sanitized — `notes` and `extracted_fields` are
  always `null` even if they were sent in the request.

Failure example (unsupported type):

```bash
curl -s -o /dev/null -w "%{http_code}\n" -X POST http://127.0.0.1:8000/api/documents/extract \
  -H "Content-Type: application/json" \
  -d '{"document_type":"k1_partnership","file_name":"k1.pdf"}'
# Expected: 422
```

## 7. /api/tax/rules (rule-data sanity)

```bash
curl -s "http://127.0.0.1:8000/api/tax/rules?tax_year=2025&state_code=CA" | python3 -m json.tool | head -20
curl -s "http://127.0.0.1:8000/api/tax/rules?tax_year=2024" | python3 -m json.tool
```

Expected:

- 2025 / CA returns `status: "ok"` with `federal` + `state` payloads.
- 2024 returns a controlled `status: "error"` with `code: "TAX_RULE_FILE_MISSING"`
  and **does not** crash or invent fallback rules.

## 8. Quick "everything together" smoke

```bash
( cd backend && python -m pytest -q ) \
  && curl -fs http://127.0.0.1:8000/api/health > /dev/null \
  && echo OK
```

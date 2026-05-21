/**
 * Mirrors the FastAPI Pydantic schemas in `backend/app/schemas.py`.
 *
 * Keep these definitions in sync with the backend; the names and casing match
 * the JSON wire format (snake_case) so request and response bodies can be
 * passed through directly.
 */

export type ApiFilingStatus =
  | "single"
  | "married_filing_jointly"
  | "married_filing_separately"
  | "head_of_household"
  | "qualifying_surviving_spouse";

export type ConfidenceLevel = "low" | "medium" | "high";
export type WarningSeverity = "info" | "low" | "medium" | "high";
export type ResponseStatus =
  | "draft"
  | "needs_more_information"
  | "review_required"
  | "error";

export type DocumentTypeCode =
  | "w2"
  | "1098_t"
  | "1099_int"
  | "1099_misc"
  | "1099_nec"
  | "other";

export interface HealthResponseBody {
  status: string;
  service: string;
}

export interface TaxpayerProfileBody {
  filing_status?: ApiFilingStatus | null;
  tax_year?: number | null;
  resident_state?: string | null;
  work_state?: string | null;
  can_be_claimed_as_dependent?: boolean | null;
  was_student?: boolean | null;
  received_1098_t?: boolean | null;
  multiple_jobs?: boolean | null;
  received_1099?: boolean | null;
  dependents_count?: number | null;
}

export interface IncomeInputBody {
  w2_wages?: string | null;
  federal_withholding?: string | null;
  state_withholding?: string | null;
  interest_income?: string | null;
  self_employment_income?: string | null;
  other_income?: string | null;
}

export interface EducationInputBody {
  is_student?: boolean | null;
  received_1098_t?: boolean | null;
  qualified_expenses?: string | null;
  scholarships_or_grants?: string | null;
  institution_name?: string | null;
}

export interface DocumentInputBody {
  document_id?: string | null;
  document_type: DocumentTypeCode;
  file_name?: string | null;
  extraction_status?: "not_started" | "parsed" | "needs_review" | "error" | null;
  extracted_fields?: Record<string, unknown> | null;
  notes?: string | null;
}

export interface TaxScenarioRequestBody {
  profile: TaxpayerProfileBody;
  income?: IncomeInputBody;
  education?: EducationInputBody;
  documents?: DocumentInputBody[];
  user_goal?: string | null;
}

export interface AgentFindingBody {
  agent_name: string;
  category: string;
  summary: string;
  confidence: ConfidenceLevel;
  rationale?: string | null;
  suggested_action?: string | null;
  supporting_documents?: string[];
}

export interface AgentWarningBody {
  severity: WarningSeverity;
  code: string;
  message: string;
  recommended_follow_up?: string | null;
}

export interface TaxAnalysisResponseBody {
  status: ResponseStatus;
  findings: AgentFindingBody[];
  warnings: AgentWarningBody[];
  next_questions: string[];
  missing_information: string[];
  disclaimer: string;
}

export interface ChatRequestBody {
  message: string;
  session_id?: string | null;
  scenario?: TaxScenarioRequestBody | null;
}

export interface ChatResponseBody {
  status: ResponseStatus;
  answer: string;
  next_questions: string[];
  warnings: AgentWarningBody[];
  missing_information: string[];
  disclaimer: string;
}

export interface TaxRulesContextBody {
  status: "ok";
  tax_year: number;
  federal: Record<string, unknown>;
  state_code?: string | null;
  state?: Record<string, unknown> | null;
  source_references: string[];
  last_reviewed: Record<string, string>;
}

export interface TaxRulesErrorBody {
  status: "error";
  code: string;
  message: string;
  rule_scope: string;
  tax_year: number;
  state_code?: string | null;
}

export type TaxRulesResponseBody = TaxRulesContextBody | TaxRulesErrorBody;

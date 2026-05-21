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
export type OpportunityImpact = "low" | "medium" | "high" | "unknown";
export type RiskLevel = "low" | "medium" | "high" | "unknown";
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

export type OpportunityCategory =
  | "deduction"
  | "credit"
  | "filing_status"
  | "state_tax"
  | "income"
  | "retirement"
  | "hsa"
  | "education"
  | "self_employment"
  | "documentation"
  | "risk"
  | "general";

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
  age?: number | null;
  is_blind?: boolean | null;
  marital_status_known?: boolean | null;
  paid_more_than_half_home_cost?: boolean | null;
}

export interface IncomeInputBody {
  w2_wages?: string | null;
  federal_withholding?: string | null;
  state_withholding?: string | null;
  interest_income?: string | null;
  self_employment_income?: string | null;
  other_income?: string | null;
  unemployment_income?: string | null;
  dividend_income?: string | null;
  capital_gain_income?: string | null;
  tip_income?: string | null;
}

export interface EducationInputBody {
  is_student?: boolean | null;
  received_1098_t?: boolean | null;
  qualified_expenses?: string | null;
  scholarships_or_grants?: string | null;
  institution_name?: string | null;
  student_loan_interest?: string | null;
  pursuit_of_degree?: boolean | null;
  half_time_student?: boolean | null;
  completed_first_four_years?: boolean | null;
  felony_drug_conviction?: boolean | null;
}

export interface DocumentInputBody {
  document_id?: string | null;
  document_type: DocumentTypeCode;
  file_name?: string | null;
  extraction_status?: "not_started" | "parsed" | "needs_review" | "error" | null;
  extracted_fields?: Record<string, unknown> | null;
  confirmed_fields?: Record<string, unknown> | null;
  file_size_bytes?: number | null;
  notes?: string | null;
}

export interface SpouseProfileBody {
  has_income?: boolean | null;
  w2_wages?: string | null;
  federal_withholding?: string | null;
  student_loan_plan?: boolean | null;
  itemizes_separately?: boolean | null;
}

export interface DependentInputBody {
  age?: number | null;
  relationship?: string | null;
  months_lived_with_taxpayer?: number | null;
  provided_over_half_support?: boolean | null;
  has_valid_ssn?: boolean | null;
  was_student?: boolean | null;
  disabled?: boolean | null;
  childcare_expenses_paid?: string | null;
}

export interface ItemizedDeductionsInputBody {
  mortgage_interest?: string | null;
  property_taxes?: string | null;
  state_local_taxes_paid?: string | null;
  charitable_cash?: string | null;
  charitable_non_cash?: string | null;
  medical_expenses?: string | null;
  gambling_losses?: string | null;
  gambling_winnings?: string | null;
}

export interface SelfEmploymentInputBody {
  gross_income?: string | null;
  expenses?: string | null;
  home_office_used_regularly_exclusively?: boolean | null;
  business_miles?: string | null;
  has_1099_nec?: boolean | null;
  made_estimated_payments?: boolean | null;
}

export interface RetirementInputBody {
  traditional_ira_contribution?: string | null;
  roth_ira_contribution?: string | null;
  employer_plan_contribution?: string | null;
  has_employer_retirement_plan?: boolean | null;
  eligible_for_savers_credit_review?: boolean | null;
}

export interface HsaInputBody {
  had_hdhp_coverage?: boolean | null;
  coverage_type?: "self_only" | "family" | null;
  hsa_contribution?: string | null;
  employer_hsa_contribution?: string | null;
}

export interface ChildcareInputBody {
  expenses?: string | null;
  care_provider_name_present?: boolean | null;
  care_provider_tax_id_present?: boolean | null;
  work_related?: boolean | null;
}

export interface CleanEnergyInputBody {
  home_energy_improvements?: string | null;
  solar_or_battery_storage?: string | null;
  clean_vehicle_purchase?: boolean | null;
  vehicle_make_model_year_present?: boolean | null;
  seller_report_available?: boolean | null;
}

export interface TaxSavingsPreferencesBody {
  priority?:
    | "maximize_refund_review"
    | "reduce_taxable_income"
    | "find_missing_documents"
    | "compare_filing_options"
    | "general_review"
    | null;
  risk_tolerance?: "low" | "medium" | "high" | null;
  wants_state_review?: boolean | null;
}

export interface TaxScenarioRequestBody {
  profile: TaxpayerProfileBody;
  income?: IncomeInputBody;
  education?: EducationInputBody;
  spouse?: SpouseProfileBody | null;
  dependents?: DependentInputBody[];
  itemized_deductions?: ItemizedDeductionsInputBody | null;
  self_employment?: SelfEmploymentInputBody | null;
  retirement?: RetirementInputBody | null;
  hsa?: HsaInputBody | null;
  childcare?: ChildcareInputBody | null;
  clean_energy?: CleanEnergyInputBody | null;
  documents?: DocumentInputBody[];
  tax_savings_preferences?: TaxSavingsPreferencesBody | null;
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

export interface TaxSavingsOpportunityBody {
  opportunity_id: string;
  agent_name: string;
  category: OpportunityCategory;
  title: string;
  summary: string;
  potential_impact: OpportunityImpact;
  confidence: ConfidenceLevel;
  required_facts: string[];
  required_documents: string[];
  estimated_directional_effect?: string | null;
  risk_level: RiskLevel;
  risk_notes: string[];
  suggested_next_step: string;
  professional_review_required: boolean;
  source_references: string[];
}

export interface TaxAnalysisResponseBody {
  status: ResponseStatus;
  findings: AgentFindingBody[];
  warnings: AgentWarningBody[];
  next_questions: string[];
  missing_information: string[];
  disclaimer: string;
}

export interface TaxOptimizationResponseBody {
  status: ResponseStatus;
  opportunities: TaxSavingsOpportunityBody[];
  warnings: AgentWarningBody[];
  missing_information: string[];
  next_questions: string[];
  review_package_summary: string;
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
  related_opportunities?: TaxSavingsOpportunityBody[];
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

import {
  mockChatReply,
} from "../data/mockData";
import type {
  ChatRequestBody,
  ChatResponseBody,
  HealthResponseBody,
  TaxAnalysisResponseBody,
  TaxOptimizationResponseBody,
  TaxRulesResponseBody,
  TaxScenarioRequestBody,
} from "../lib/apiTypes";

export class ApiError extends Error {
  status: number;
  detail: unknown;

  constructor(message: string, status: number, detail?: unknown) {
    super(message);
    this.name = "ApiError";
    this.status = status;
    this.detail = detail;
  }
}

const DEFAULT_BASE_URL = "/api";

function envFlag(value: unknown): boolean {
  return typeof value === "string" && value.toLowerCase() === "true";
}

export function isBackendEnabled(): boolean {
  return envFlag(import.meta.env.VITE_USE_BACKEND);
}

function baseUrl(): string {
  const fromEnv = import.meta.env.VITE_API_BASE_URL;
  if (typeof fromEnv === "string" && fromEnv.length > 0) {
    return fromEnv.replace(/\/+$/, "");
  }
  return DEFAULT_BASE_URL;
}

async function request<T>(
  path: string,
  init: RequestInit & { signal?: AbortSignal } = {},
): Promise<T> {
  const url = `${baseUrl()}${path}`;
  const headers = new Headers(init.headers);
  if (init.body && !headers.has("Content-Type")) {
    headers.set("Content-Type", "application/json");
  }

  let response: Response;
  try {
    response = await fetch(url, { ...init, headers });
  } catch (err) {
    throw new ApiError(
      err instanceof Error ? err.message : "Network request failed",
      0,
    );
  }

  const text = await response.text();
  let parsed: unknown = undefined;
  if (text.length > 0) {
    try {
      parsed = JSON.parse(text);
    } catch {
      parsed = text;
    }
  }

  if (!response.ok) {
    throw new ApiError(
      `Request to ${path} failed (${response.status})`,
      response.status,
      parsed,
    );
  }

  return parsed as T;
}

export function getHealth(signal?: AbortSignal): Promise<HealthResponseBody> {
  if (!isBackendEnabled()) {
    return Promise.resolve({
      status: "ok",
      service: "Mock mode",
    });
  }

  return request<HealthResponseBody>("/health", { method: "GET", signal });
}

export function postChat(
  body: ChatRequestBody,
  signal?: AbortSignal,
): Promise<ChatResponseBody> {
  if (!isBackendEnabled()) {
    return Promise.resolve(buildMockChatResponse(body));
  }

  return request<ChatResponseBody>("/chat", {
    method: "POST",
    body: JSON.stringify(body),
    signal,
  });
}

export function postAnalyze(
  body: TaxScenarioRequestBody,
  signal?: AbortSignal,
): Promise<TaxAnalysisResponseBody> {
  if (!isBackendEnabled()) {
    return Promise.resolve(buildMockTaxAnalysisResponse(body));
  }

  return request<TaxAnalysisResponseBody>("/tax/analyze", {
    method: "POST",
    body: JSON.stringify(body),
    signal,
  });
}

export function postOptimize(
  body: TaxScenarioRequestBody,
  signal?: AbortSignal,
): Promise<TaxOptimizationResponseBody> {
  if (!isBackendEnabled()) {
    return Promise.resolve(buildMockTaxOptimizationResponse(body));
  }

  return request<TaxOptimizationResponseBody>("/tax/optimize", {
    method: "POST",
    body: JSON.stringify(body),
    signal,
  });
}

export function getTaxRules(
  taxYear: number,
  stateCode?: string | null,
  signal?: AbortSignal,
): Promise<TaxRulesResponseBody> {
  if (!isBackendEnabled()) {
    return Promise.resolve(buildMockTaxRulesResponse(taxYear, stateCode));
  }

  const params = new URLSearchParams({ tax_year: String(taxYear) });
  if (stateCode) params.set("state_code", stateCode.toUpperCase());
  return request<TaxRulesResponseBody>(`/tax/rules?${params.toString()}`, {
    method: "GET",
    signal,
  });
}

function buildMockChatResponse(body: ChatRequestBody): ChatResponseBody {
  const answer = mockChatReply(body.message);
  const scenario = body.scenario;

  if (!scenario) {
    return {
      status: "draft",
      answer,
      next_questions: [
        "Which tax year would you like to review?",
        "Do you have your W-2 or other tax documents ready?",
      ],
      warnings: [],
      missing_information: [],
      disclaimer:
        "TaxMax AI provides AI-assisted preparation support and does not provide legal, tax, or financial advice. Review all information with a qualified professional before filing.",
    };
  }

  const warnings: ChatResponseBody["warnings"] = [];
  const missing_information: string[] = [];
  const next_questions: string[] = [];

  if (scenario.profile.tax_year == null) {
    missing_information.push("Tax year");
    next_questions.push("Which tax year should I review?");
  }
  if (scenario.profile.filing_status == null) {
    missing_information.push("Filing status");
    next_questions.push("What filing status are you considering?");
  }
  if (
    scenario.profile.was_student === true &&
    scenario.profile.received_1098_t == null
  ) {
    missing_information.push("Form 1098-T status");
    next_questions.push("Did you receive a Form 1098-T from your school?");
    warnings.push({
      severity: "low",
      code: "MISSING_1098_T_STATUS",
      message: "Student status was indicated but 1098-T receipt is unknown.",
      recommended_follow_up: "Ask whether the user received Form 1098-T.",
    });
  }

  return {
    status: missing_information.length > 0 ? "needs_more_information" : "draft",
    answer,
    next_questions: dedupeStrings(next_questions),
    warnings,
    missing_information: dedupeStrings(missing_information),
    disclaimer:
      "TaxMax AI provides AI-assisted preparation support and does not provide legal, tax, or financial advice. Review all information with a qualified professional before filing.",
  };
}

function buildMockTaxAnalysisResponse(
  body: TaxScenarioRequestBody,
): TaxAnalysisResponseBody {
  const findings: TaxAnalysisResponseBody["findings"] = [];
  const warnings: TaxAnalysisResponseBody["warnings"] = [];
  const nextQuestions: string[] = [];
  const missingInformation: string[] = [];
  const profile = body.profile;
  const income = body.income;
  const education = body.education;
  const documents = body.documents ?? [];

  if (profile.tax_year == null) {
    missingInformation.push("Tax year");
    nextQuestions.push("Which tax year should I review?");
    warnings.push({
      severity: "medium",
      code: "MISSING_TAX_YEAR",
      message: "Tax year is required before a review can be completed.",
      recommended_follow_up: "Ask the user which tax year should be reviewed.",
    });
  }

  if (profile.filing_status == null) {
    missingInformation.push("Filing status");
    nextQuestions.push("What filing status are you considering?");
    warnings.push({
      severity: "medium",
      code: "MISSING_FILING_STATUS",
      message: "Filing status is missing and may affect the review.",
      recommended_follow_up: "Ask the user to confirm their expected filing status.",
    });
  }

  if (profile.resident_state == null) {
    missingInformation.push("Resident state");
    nextQuestions.push("What is your resident state?");
    warnings.push({
      severity: "medium",
      code: "MISSING_RESIDENT_STATE",
      message: "Resident state is missing and state review requires confirmation.",
      recommended_follow_up: "Ask the user for their resident state.",
    });
  } else {
    findings.push({
      agent_name: "State Tax Agent",
      category: "state",
      summary:
        `${profile.resident_state.toUpperCase()} state review may apply and requires confirmation against state-specific rules.`,
      confidence: "medium",
      rationale: "Resident state information was supplied.",
      suggested_action:
        "Use the resident state as review context until verified rule details are loaded.",
      supporting_documents: [],
    });
  }

  if (profile.can_be_claimed_as_dependent == null) {
    warnings.push({
      severity: "medium",
      code: "MISSING_DEPENDENCY_CONTEXT",
      message: "Dependency status has not been confirmed.",
      recommended_follow_up:
        "Ask whether another taxpayer can claim the user as a dependent.",
    });
    nextQuestions.push(
      "Can another taxpayer claim you as a dependent for the tax year?",
    );
    missingInformation.push("Dependency status");
  }

  if (income == null) {
    missingInformation.push("Income inputs");
    nextQuestions.push("Do you have W-2 or 1099 income to review?");
    warnings.push({
      severity: "medium",
      code: "MISSING_INCOME_INPUTS",
      message: "Income inputs are missing.",
      recommended_follow_up: "Confirm whether the user had W-2 wages or 1099 income.",
    });
  } else {
    if (income.w2_wages != null) {
      findings.push({
        agent_name: "Income Agent",
        category: "income",
        summary:
          "W-2 wage information was supplied and should be reviewed against the source W-2.",
        confidence: "medium",
        rationale: "W-2 wage input was present.",
        suggested_action:
          "Confirm Box 1 and withholding details before deeper review.",
        supporting_documents: [],
      });
    }

    if (income.w2_wages == null && income.self_employment_income == null) {
      warnings.push({
        severity: "medium",
        code: "MISSING_INCOME_INPUTS",
        message: "No wage or self-employment income has been provided.",
        recommended_follow_up:
          "Confirm whether the user had W-2 wages, 1099 income, or both.",
      });
    }
  }

  const educationRelevant =
    profile.was_student === true ||
    profile.received_1098_t === true ||
    education?.is_student === true ||
    education?.received_1098_t === true;

  if (educationRelevant) {
    findings.push({
      agent_name: "Education Agent",
      category: "education",
      summary:
        "Education inputs appear relevant and should be reviewed with Form 1098-T details.",
      confidence: "medium",
      rationale: "Student status or 1098-T receipt was indicated.",
      suggested_action:
        "Confirm school, qualified expenses, scholarships, and dependency status.",
      supporting_documents: [],
    });

    if (education?.qualified_expenses == null) {
      missingInformation.push("Qualified education expenses");
      nextQuestions.push("What qualified education expenses did you pay?");
    }

    if (profile.received_1098_t == null && education?.received_1098_t == null) {
      warnings.push({
        severity: "low",
        code: "MISSING_1098_T_STATUS",
        message:
          "Student status is present, but Form 1098-T receipt is unknown.",
        recommended_follow_up: "Ask whether the user received Form 1098-T.",
      });
    }
  }

  for (const document of documents) {
    if (document.extraction_status === "needs_review") {
      findings.push({
        agent_name: "Document Agent",
        category: "documents",
        summary: `Document ${document.file_name ?? document.document_id ?? document.document_type} has extracted fields that need user review.`,
        confidence: "low",
        rationale: "Document extraction status is marked needs_review.",
        suggested_action: "Verify each extracted field against the source document.",
        supporting_documents: document.document_id ? [document.document_id] : [],
      });
    }
    if (document.extraction_status === "error") {
      warnings.push({
        severity: "high",
        code: "DOCUMENT_EXTRACTION_ERROR",
        message: `Extraction error for document ${document.file_name ?? document.document_id ?? document.document_type}.`,
        recommended_follow_up:
          "Ask the user to re-upload the document or enter values manually.",
      });
    }
  }

  if (findings.length === 0) {
    findings.push({
      agent_name: "Summary Agent",
      category: "summary",
      summary:
        "Initial review context is present and can be refined as more facts are confirmed.",
      confidence: "low",
      rationale: "Mock analysis uses only the currently supplied scenario fields.",
      suggested_action:
        "Continue collecting and confirming documents before filing decisions.",
      supporting_documents: [],
    });
  }

  const status: TaxAnalysisResponseBody["status"] =
    missingInformation.length > 0
      ? "needs_more_information"
      : warnings.length > 0
        ? "review_required"
        : "draft";

  return {
    status,
    findings,
    warnings,
    next_questions: dedupeStrings(nextQuestions),
    missing_information: dedupeStrings(missingInformation),
    disclaimer:
      "TaxMax AI provides AI-assisted preparation support and does not provide legal, tax, or financial advice. Review all information with a qualified professional before filing.",
  };
}

function buildMockTaxOptimizationResponse(
  body: TaxScenarioRequestBody,
): TaxOptimizationResponseBody {
  const opportunities: TaxOptimizationResponseBody["opportunities"] = [];
  const missing_information: string[] = [];
  const next_questions: string[] = [];
  const warnings: TaxOptimizationResponseBody["warnings"] = [];
  const profile = body.profile;
  const income = body.income;
  const education = body.education;
  const documents = body.documents ?? [];

  if (profile.filing_status == null) {
    missing_information.push("Filing status");
    next_questions.push("Which filing status are you considering?");
  }
  if (profile.resident_state == null) {
    missing_information.push("Resident state");
    next_questions.push("What was your resident state for the tax year?");
  }
  if (profile.can_be_claimed_as_dependent == null) {
    missing_information.push("Dependency status");
    next_questions.push("Can another taxpayer claim you as a dependent?");
    warnings.push({
      severity: "medium",
      code: "OPTIMIZATION_DEPENDENCY_UNKNOWN",
      message:
        "Dependency status is needed before credit and education opportunities can be reviewed safely.",
      recommended_follow_up:
        "Confirm whether another taxpayer can claim the user.",
    });
  }

  if (education?.qualified_expenses != null || profile.received_1098_t === true) {
    opportunities.push({
      opportunity_id: "credit_education_review",
      agent_name: "Credit Discovery Agent",
      category: "credit",
      title: "Review education credits",
      summary:
        "Student or 1098-T facts are present, so education credit review may apply if requirements are confirmed.",
      potential_impact: "medium",
      confidence: "medium",
      required_facts: [
        "Dependency status",
        "Qualified expenses",
        "Scholarships or grants",
      ],
      required_documents: ["Form 1098-T", "School account statement"],
      estimated_directional_effect:
        "May reduce tax if credit requirements are confirmed.",
      risk_level: "medium",
      risk_notes: [
        "Education credits require exact student, institution, and dependency facts.",
      ],
      suggested_next_step:
        "Confirm 1098-T details and student eligibility facts before professional review.",
      professional_review_required: true,
      source_references: ["Mock mode"],
    });
  }

  if (income?.self_employment_income != null) {
    opportunities.push({
      opportunity_id: "deduction_self_employment_expenses",
      agent_name: "Deduction Discovery Agent",
      category: "self_employment",
      title: "Review self-employment expense documentation",
      summary:
        "Self-employment income is present, so ordinary and necessary business expenses may need review.",
      potential_impact: "high",
      confidence: "medium",
      required_facts: ["Gross business income", "Expense categories"],
      required_documents: ["1099 records", "Receipts", "Mileage log if relevant"],
      estimated_directional_effect:
        "May reduce net self-employment income if expenses are allowable and documented.",
      risk_level: "medium",
      risk_notes: ["Self-employment deductions need strong records."],
      suggested_next_step:
        "Organize income records, receipts, and mileage before professional review.",
      professional_review_required: true,
      source_references: ["Mock mode"],
    });
  }

  if (profile.resident_state != null) {
    opportunities.push({
      opportunity_id: `state_${profile.resident_state.toLowerCase()}_review`,
      agent_name: "State Tax Optimization Agent",
      category: "state_tax",
      title: `Review ${profile.resident_state.toUpperCase()} state tax opportunities`,
      summary:
        "Resident-state facts are present, so state-specific deductions, credits, and itemized deduction differences may be worth reviewing.",
      potential_impact: "medium",
      confidence: "medium",
      required_facts: ["Resident state", "Work state", "State withholding"],
      required_documents: ["State withholding forms"],
      estimated_directional_effect:
        "May affect state taxable income or credits if state-specific rules apply.",
      risk_level: "medium",
      risk_notes: ["State rules can differ from federal rules."],
      suggested_next_step:
        "Review resident and work-state facts against state instructions before filing.",
      professional_review_required: true,
      source_references: ["Mock mode"],
    });
  }

  if (documents.some((doc) => doc.extraction_status === "needs_review")) {
    opportunities.push({
      opportunity_id: "documentation_confirm_extracted_fields",
      agent_name: "Risk Review Agent",
      category: "documentation",
      title: "Confirm document fields before claiming opportunities",
      summary:
        "One or more documents still need review before extracted values are treated as reliable for savings analysis.",
      potential_impact: "unknown",
      confidence: "high",
      required_facts: ["User-confirmed extracted values"],
      required_documents: documents
        .filter((doc) => doc.extraction_status === "needs_review")
        .map((doc) => doc.file_name ?? doc.document_type),
      estimated_directional_effect:
        "Confirming documents can improve the reliability of deduction and credit review.",
      risk_level: "high",
      risk_notes: ["Unconfirmed extracted values can lead to incorrect review results."],
      suggested_next_step:
        "Compare extracted fields against the original documents and confirm or correct them.",
      professional_review_required: true,
      source_references: ["Mock mode"],
    });
  }

  if (opportunities.length === 0) {
    opportunities.push({
      opportunity_id: "general_add_more_details",
      agent_name: "Final Savings Strategy Agent",
      category: "general",
      title: "Add more details for a deeper savings review",
      summary:
        "TaxMax AI needs more income, deduction, credit, dependent, education, or state facts to surface specific savings opportunities.",
      potential_impact: "unknown",
      confidence: "low",
      required_facts: ["Income", "Filing status", "Deductions", "Credits"],
      required_documents: ["W-2", "1099 forms", "1098-T if applicable"],
      estimated_directional_effect:
        "More complete facts may reveal review opportunities.",
      risk_level: "unknown",
      risk_notes: ["Insufficient facts limit savings review."],
      suggested_next_step:
        "Complete the profile and add documents or manual values.",
      professional_review_required: true,
      source_references: ["Mock mode"],
    });
  }

  return {
    status:
      missing_information.length > 0
        ? "needs_more_information"
        : opportunities.some((item) => item.risk_level === "medium" || item.risk_level === "high")
          ? "review_required"
          : "draft",
    opportunities,
    warnings,
    missing_information: dedupeStrings(missing_information),
    next_questions: dedupeStrings(next_questions),
    review_package_summary:
      "TaxMax AI identified potential legal tax-savings review areas. Confirm all facts with a qualified tax professional before filing.",
    disclaimer:
      "TaxMax AI identifies potential legal tax-saving opportunities for review. It does not provide legal, tax, or financial advice and does not guarantee a refund, lower tax, or eligibility for any deduction or credit.",
  };
}

function buildMockTaxRulesResponse(
  taxYear: number,
  stateCode?: string | null,
): TaxRulesResponseBody {
  return {
    status: "ok",
    tax_year: taxYear,
    federal: {
      jurisdiction: "US",
      scope: "federal",
      tax_year: taxYear,
      last_reviewed: "mock",
      source_references: ["Mock mode"],
      standard_deduction: {
        status: "placeholder",
        todo: "Mock mode does not expose verified bracket data.",
      },
      tax_brackets: {
        status: "placeholder",
        todo: "Mock mode does not expose verified bracket data.",
      },
    },
    state_code: stateCode ? stateCode.toUpperCase() : null,
    state: stateCode
      ? {
          jurisdiction: stateCode.toUpperCase(),
          scope: "state",
          tax_year: taxYear,
          last_reviewed: "mock",
          source_references: ["Mock mode"],
        }
      : null,
    source_references: ["Mock mode"],
    last_reviewed: {
      federal: "mock",
      ...(stateCode ? { state: "mock" } : {}),
    },
  };
}

function dedupeStrings(values: string[]): string[] {
  return [...new Set(values)];
}

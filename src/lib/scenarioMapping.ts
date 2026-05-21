import type {
  ManualEntryData,
  T1098Review,
  TaxProfile,
  UploadedDocument,
  W2Review,
  FilingStatus as UiFilingStatus,
  YesNo,
} from "../types";
import type {
  ApiFilingStatus,
  DocumentInputBody,
  DocumentTypeCode,
  EducationInputBody,
  IncomeInputBody,
  TaxScenarioRequestBody,
  TaxpayerProfileBody,
} from "./apiTypes";

const FILING_STATUS_TO_API: Record<
  Exclude<UiFilingStatus, null>,
  ApiFilingStatus
> = {
  single: "single",
  mfj: "married_filing_jointly",
  mfs: "married_filing_separately",
  hoh: "head_of_household",
  qss: "qualifying_surviving_spouse",
};

function yesNoToBool(value: YesNo): boolean | null {
  if (value === "yes") return true;
  if (value === "no") return false;
  return null;
}

function parseMoney(input: string | null | undefined): string | null {
  if (!input) return null;
  const cleaned = input.replace(/[^0-9.-]/g, "");
  if (!cleaned) return null;
  const n = Number(cleaned);
  if (!Number.isFinite(n) || n < 0) return null;
  return n.toFixed(2);
}

function findFieldValue(
  fields: { id: string; value: string }[] | undefined,
  id: string,
): string | undefined {
  return fields?.find((f) => f.id === id)?.value;
}

function pickStateCode(value: string | null | undefined): string | null {
  if (!value) return null;
  const trimmed = value.trim().toUpperCase();
  if (trimmed.length !== 2) return null;
  return trimmed;
}

const DOCUMENT_KIND_MAP: Record<UploadedDocument["kind"], DocumentTypeCode> = {
  "W-2": "w2",
  "1098-T": "1098_t",
  "1099-INT": "1099_int",
  Other: "other",
};

interface BuildScenarioOptions {
  profile: TaxProfile;
  manual: ManualEntryData;
  w2: W2Review | null;
  t1098: T1098Review | null;
  documents: UploadedDocument[];
  /** Default tax year for the scenario when the UI does not collect one yet. */
  taxYear?: number;
  /** Optional override for resident state when not yet collected. */
  residentState?: string;
  userGoal?: string;
}

export function buildScenarioRequest(
  options: BuildScenarioOptions,
): TaxScenarioRequestBody {
  const { profile, manual, w2, t1098, documents, taxYear, residentState, userGoal } =
    options;

  const apiProfile: TaxpayerProfileBody = {
    filing_status:
      profile.filingStatus !== null
        ? FILING_STATUS_TO_API[profile.filingStatus]
        : null,
    tax_year: taxYear ?? null,
    resident_state:
      pickStateCode(residentState) ?? pickStateCode(manual.personal.state),
    work_state: null,
    can_be_claimed_as_dependent: yesNoToBool(profile.canBeClaimedAsDependent),
    was_student: yesNoToBool(profile.wasStudent),
    received_1098_t: yesNoToBool(profile.received1098T),
    multiple_jobs: yesNoToBool(profile.multipleJobs),
    received_1099: yesNoToBool(profile.received1099),
    dependents_count: null,
  };

  const wagesValue = parseMoney(findFieldValue(w2?.fields, "wages") ?? manual.w2Wages);
  const fedTaxValue = parseMoney(
    findFieldValue(w2?.fields, "fedTax") ?? manual.federalWithholding,
  );

  const income: IncomeInputBody = {
    w2_wages: wagesValue,
    federal_withholding: fedTaxValue,
    state_withholding: null,
    interest_income: null,
    self_employment_income: null,
    other_income: null,
  };

  const tuitionValue = parseMoney(
    findFieldValue(t1098?.fields, "tuition") ?? manual.educationExpenses,
  );
  const scholarshipsValue = parseMoney(
    findFieldValue(t1098?.fields, "scholarships"),
  );
  const institutionName = findFieldValue(t1098?.fields, "school");

  const educationRelevant =
    profile.wasStudent === "yes" ||
    profile.received1098T === "yes" ||
    manual.isStudent === "yes" ||
    !!t1098 ||
    !!tuitionValue;

  const education: EducationInputBody | undefined = educationRelevant
    ? {
        is_student: yesNoToBool(profile.wasStudent ?? manual.isStudent),
        received_1098_t: yesNoToBool(profile.received1098T),
        qualified_expenses: tuitionValue,
        scholarships_or_grants: scholarshipsValue,
        institution_name: institutionName ?? null,
      }
    : undefined;

  const documentBodies: DocumentInputBody[] = documents.map((doc) => ({
    document_id: doc.id,
    document_type: DOCUMENT_KIND_MAP[doc.kind] ?? "other",
    file_name: doc.name,
    extraction_status:
      doc.status === "parsing"
        ? "not_started"
        : doc.status === "parsed"
          ? "parsed"
          : "error",
    extracted_fields: null,
    confirmed_fields:
      doc.kind === "W-2" && w2
        ? Object.fromEntries(w2.fields.map((field) => [field.id, field.value]))
        : doc.kind === "1098-T" && t1098
          ? Object.fromEntries(t1098.fields.map((field) => [field.id, field.value]))
          : null,
    file_size_bytes: doc.sizeBytes,
    notes: null,
  }));

  return {
    profile: apiProfile,
    income,
    education,
    dependents: [],
    itemized_deductions: null,
    self_employment:
      profile.received1099 === "yes"
        ? {
            gross_income: null,
            expenses: null,
            home_office_used_regularly_exclusively: null,
            business_miles: null,
            has_1099_nec: true,
            made_estimated_payments: null,
          }
        : null,
    retirement: {
      traditional_ira_contribution: null,
      roth_ira_contribution: null,
      employer_plan_contribution: null,
      has_employer_retirement_plan: null,
      eligible_for_savers_credit_review:
        manual.credits.savingsContributionsCredit || null,
    },
    hsa: null,
    childcare:
      manual.credits.childTaxCredit
        ? {
            expenses: null,
            care_provider_name_present: null,
            care_provider_tax_id_present: null,
            work_related: null,
          }
        : null,
    clean_energy: null,
    documents: documentBodies,
    tax_savings_preferences: {
      priority: "maximize_refund_review",
      risk_tolerance: "low",
      wants_state_review: true,
    },
    user_goal: userGoal ?? null,
  };
}

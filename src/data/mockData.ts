import type {
  ManualEntryData,
  ReviewField,
  T1098Review,
  TaxProfile,
  W2Review,
} from "../types";

export const MOCK_W2_FIELDS: ReviewField[] = [
  {
    id: "employer",
    label: "Employer name",
    value: "Acme Technologies Inc.",
    source: "W-2 Box c",
    confirmed: false,
  },
  {
    id: "ein",
    label: "Employer EIN",
    value: "12-3456789",
    source: "W-2 Box b",
    confirmed: false,
  },
  {
    id: "wages",
    label: "Wages, tips, and compensation",
    value: "$42,350.00",
    source: "W-2 Box 1",
    confirmed: false,
  },
  {
    id: "fedTax",
    label: "Federal income tax withheld",
    value: "$4,280.00",
    source: "W-2 Box 2",
    confirmed: false,
  },
  {
    id: "ssWages",
    label: "Social Security wages",
    value: "$42,350.00",
    source: "W-2 Box 3",
    confirmed: false,
  },
  {
    id: "medicareWages",
    label: "Medicare wages",
    value: "$42,350.00",
    source: "W-2 Box 5",
    confirmed: false,
  },
];

export const MOCK_1098T_FIELDS: ReviewField[] = [
  {
    id: "school",
    label: "School",
    value: "Columbia University",
    source: "1098-T Filer",
    confirmed: false,
  },
  {
    id: "tuition",
    label: "Tuition payments",
    value: "$18,500.00",
    source: "1098-T Box 1",
    confirmed: false,
  },
  {
    id: "scholarships",
    label: "Scholarships / grants",
    value: "$7,500.00",
    source: "1098-T Box 5",
    confirmed: false,
  },
];

export const buildMockW2Review = (documentId: string): W2Review => ({
  documentId,
  fields: MOCK_W2_FIELDS.map((f) => ({ ...f })),
});

export const buildMock1098TReview = (documentId: string): T1098Review => ({
  documentId,
  fields: MOCK_1098T_FIELDS.map((f) => ({ ...f })),
});

export const EMPTY_MANUAL_ENTRY: ManualEntryData = {
  personal: {
    firstName: "",
    lastName: "",
    ssn: "",
    dateOfBirth: "",
    email: "",
    address: "",
    city: "",
    state: "",
    zip: "",
  },
  filingStatus: null,
  w2Wages: "",
  federalWithholding: "",
  educationExpenses: "",
  isStudent: null,
  credits: {
    earnedIncomeCredit: false,
    childTaxCredit: false,
    educationCredit: false,
    savingsContributionsCredit: false,
  },
};

export const EMPTY_TAX_PROFILE: TaxProfile = {
  filingStatus: null,
  canBeClaimedAsDependent: null,
  wasStudent: null,
  received1098T: null,
  multipleJobs: null,
  received1099: null,
};

export const SUGGESTED_PROMPTS = [
  "What is a W-2?",
  "Where do I find Box 1?",
  "Do I need a 1098-T?",
  "Can someone claim me as a dependent?",
  "Why do I need to review extracted data?",
  "What documents should I upload?",
];

const MOCK_REPLY_MAP: { match: RegExp; reply: string }[] = [
  {
    match: /w-?2/i,
    reply:
      "A W-2 is the wage statement your employer sends each January. It reports your wages and the federal, state, Social Security, and Medicare taxes that were withheld. Box 1 shows your total taxable wages, and Box 2 shows the federal income tax that was withheld.",
  },
  {
    match: /box ?1/i,
    reply:
      "Box 1 of your W-2 is in the upper right area of the form and is labeled “Wages, tips, other compensation.” That number is your federal taxable wages for the year.",
  },
  {
    match: /1098-?t/i,
    reply:
      "A 1098-T reports tuition payments and scholarships from an eligible educational institution. You generally need it if you (or a dependent) were enrolled in higher education and want to explore education credits like the American Opportunity Credit or Lifetime Learning Credit.",
  },
  {
    match: /dependent/i,
    reply:
      "Whether someone can claim you as a dependent depends on factors like age, student status, residency, and financial support. Based on your answers, I can highlight the requirements to review with a qualified tax professional.",
  },
  {
    match: /review|extracted|parse/i,
    reply:
      "Document parsing can sometimes misread numbers, especially on scanned PDFs. Reviewing each extracted value before moving forward is the easiest way to catch typos and make sure your return reflects your actual documents.",
  },
  {
    match: /upload|document/i,
    reply:
      "For most simple returns, you’ll want your W-2 from each employer, any 1099 forms (1099-INT, 1099-NEC, 1099-DIV), and a 1098-T if you paid tuition. You can also enter information manually if you don’t have the PDFs.",
  },
  {
    match: /refund|owe|estimate/i,
    reply:
      "The summary screen shows a rough estimate based on the information you’ve entered. It’s not final — your actual refund or balance due depends on the full return and a complete review.",
  },
];

const DEFAULT_REPLY =
  "I can explain tax terms and walk you through this app step by step. Try asking about W-2s, 1098-Ts, filing status, or how the review step works. For anything specific to your situation, please confirm with a qualified tax professional.";

export function mockChatReply(userMessage: string): string {
  for (const { match, reply } of MOCK_REPLY_MAP) {
    if (match.test(userMessage)) return reply;
  }
  return DEFAULT_REPLY;
}

export const STEP_CONTEXT_HINTS: Record<string, string> = {
  welcome:
    "Welcome! Choose document upload if you have PDFs ready, or manual entry to type in your information.",
  upload:
    "Drag and drop your W-2, 1098-T, or 1099 forms. I’ll walk you through what was extracted next.",
  manual:
    "Fill in the fields you have on hand. You can come back and edit anything before the final review.",
  review:
    "Check each extracted field against your original document. Confirm what looks right, edit what doesn’t.",
  profile:
    "These questions help shape your return. Answer honestly — I won’t make a final determination, just guide you.",
  summary:
    "This is an estimate based on what you’ve entered. The final review step covers everything before you wrap up.",
  final:
    "Take one last look at every section. When everything shows Complete, you can prepare your review package.",
};

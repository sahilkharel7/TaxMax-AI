export type StepId =
  | "welcome"
  | "upload"
  | "manual"
  | "review"
  | "profile"
  | "summary"
  | "final";

export type FilingStatus =
  | "single"
  | "mfj"
  | "mfs"
  | "hoh"
  | "qss"
  | null;

export type YesNo = "yes" | "no" | null;

export interface PersonalInfo {
  firstName: string;
  lastName: string;
  ssn: string;
  dateOfBirth: string;
  email: string;
  address: string;
  city: string;
  state: string;
  zip: string;
}

export interface ManualEntryData {
  personal: PersonalInfo;
  filingStatus: FilingStatus;
  w2Wages: string;
  federalWithholding: string;
  educationExpenses: string;
  isStudent: YesNo;
  credits: {
    earnedIncomeCredit: boolean;
    childTaxCredit: boolean;
    educationCredit: boolean;
    savingsContributionsCredit: boolean;
  };
}

export interface TaxProfile {
  filingStatus: FilingStatus;
  canBeClaimedAsDependent: YesNo;
  wasStudent: YesNo;
  received1098T: YesNo;
  multipleJobs: YesNo;
  received1099: YesNo;
}

export type DocumentKind = "W-2" | "1098-T" | "1099-INT" | "Other";

export interface UploadedDocument {
  id: string;
  name: string;
  kind: DocumentKind;
  sizeBytes: number;
  uploadedAt: number;
  status: "parsing" | "parsed" | "error";
}

export interface ReviewField {
  id: string;
  label: string;
  value: string;
  source: string;
  confirmed: boolean;
}

export interface W2Review {
  documentId: string;
  fields: ReviewField[];
}

export interface T1098Review {
  documentId: string;
  fields: ReviewField[];
}

export interface ChatMessage {
  id: string;
  role: "user" | "assistant";
  content: string;
}

import { useMemo } from "react";
import type {
  ManualEntryData,
  T1098Review,
  TaxProfile,
  UploadedDocument,
  W2Review,
} from "../types";
import { Button } from "../components/ui/Button";
import { Card, SectionHeader } from "../components/ui/Card";
import { StatusBadge, type StatusTone } from "../components/ui/StatusBadge";
import { useTaxAnalysis } from "../hooks/useTaxAnalysis";
import { buildScenarioRequest } from "../lib/scenarioMapping";
import type { AgentWarningBody } from "../lib/apiTypes";

interface FinalReviewProps {
  w2: W2Review | null;
  t1098: T1098Review | null;
  manual: ManualEntryData;
  profile: TaxProfile;
  documents: UploadedDocument[];
  taxYear?: number;
  onBack: () => void;
  onPrepare: () => void;
  prepared: boolean;
}

interface SectionStatus {
  tone: StatusTone;
  label: string;
}

function personalStatus(manual: ManualEntryData): SectionStatus {
  const p = manual.personal;
  const filled = [p.firstName, p.lastName, p.dateOfBirth, p.state].filter(
    Boolean,
  ).length;
  if (filled === 0) return { tone: "missing", label: "Missing information" };
  if (filled < 4) return { tone: "review", label: "Needs review" };
  return { tone: "complete", label: "Complete" };
}

function incomeStatus(
  w2: W2Review | null,
  manual: ManualEntryData,
): SectionStatus {
  const hasW2Doc = !!w2 && w2.fields.every((f) => f.confirmed);
  const hasManual = !!manual.w2Wages;
  if (hasW2Doc) return { tone: "complete", label: "Complete" };
  if (hasManual) return { tone: "review", label: "Needs review" };
  return { tone: "missing", label: "Missing information" };
}

function educationStatus(
  t1098: T1098Review | null,
  manual: ManualEntryData,
  profile: TaxProfile,
): SectionStatus {
  const wantsEducation =
    profile.received1098T === "yes" || profile.wasStudent === "yes";
  if (!wantsEducation) return { tone: "neutral", label: "Not applicable" };
  const hasDoc = !!t1098 && t1098.fields.every((f) => f.confirmed);
  const hasManual = !!manual.educationExpenses;
  if (hasDoc) return { tone: "complete", label: "Complete" };
  if (hasManual) return { tone: "review", label: "Needs review" };
  return { tone: "missing", label: "Missing information" };
}

function creditsStatus(manual: ManualEntryData): SectionStatus {
  const anyChecked = Object.values(manual.credits).some(Boolean);
  return anyChecked
    ? { tone: "review", label: "Needs review" }
    : { tone: "neutral", label: "None selected" };
}

function documentsStatus(documents: UploadedDocument[]): SectionStatus {
  if (documents.length === 0)
    return { tone: "neutral", label: "No documents" };
  if (documents.every((d) => d.status === "parsed"))
    return { tone: "complete", label: "Complete" };
  return { tone: "review", label: "Needs review" };
}

export function FinalReview({
  w2,
  t1098,
  manual,
  profile,
  documents,
  taxYear = 2025,
  onBack,
  onPrepare,
  prepared,
}: FinalReviewProps) {
  const personal = personalStatus(manual);
  const income = incomeStatus(w2, manual);
  const education = educationStatus(t1098, manual, profile);
  const credits = creditsStatus(manual);
  const docs = documentsStatus(documents);

  const localWarnings: string[] = [];
  if (income.tone === "missing")
    localWarnings.push("No income information found.");
  if (
    profile.received1098T === "yes" &&
    education.tone !== "complete"
  )
    localWarnings.push("You indicated a 1098-T but it isn’t fully reviewed.");
  if (
    profile.received1099 === "yes" &&
    !documents.some((d) => d.kind === "1099-INT")
  )
    localWarnings.push("You indicated a 1099 form but none was uploaded.");

  const scenarioCacheKey = useMemo(
    () =>
      JSON.stringify({
        profile,
        manual,
        w2,
        t1098,
        documents: documents.map((d) => ({
          id: d.id,
          kind: d.kind,
          status: d.status,
        })),
        taxYear,
      }),
    [profile, manual, w2, t1098, documents, taxYear],
  );

  const analysis = useTaxAnalysis({
    cacheKey: scenarioCacheKey,
    buildScenario: () =>
      buildScenarioRequest({
        profile,
        manual,
        w2,
        t1098,
        documents,
        taxYear,
        userGoal: "Final review checklist before preparing review package.",
      }),
  });

  const rows: { title: string; description: string; status: SectionStatus }[] =
    [
      {
        title: "Personal info",
        description: "Name, address, filing status",
        status: personal,
      },
      {
        title: "Income",
        description: "Wages, withholding, W-2 details",
        status: income,
      },
      {
        title: "Education",
        description: "1098-T, tuition, scholarships",
        status: education,
      },
      {
        title: "Credits",
        description: "EITC, CTC, education, saver’s",
        status: credits,
      },
      {
        title: "Documents",
        description: `${documents.length} uploaded`,
        status: docs,
      },
    ];

  const apiWarnings = analysis.status === "success" ? analysis.data.warnings : [];
  const apiMissing =
    analysis.status === "success" ? analysis.data.missing_information : [];
  const noWarnings =
    localWarnings.length === 0 && apiWarnings.length === 0 && apiMissing.length === 0;

  return (
    <div className="animate-fade-up mx-auto w-full max-w-3xl space-y-6 px-4 py-8 sm:py-10">
      <SectionHeader
        eyebrow="Step 7"
        title="Final review"
        description="One last pass. Make sure every section reads Complete before you prepare your review package."
      />

      <Card padded={false}>
        <ul className="divide-y divide-slate-100">
          {rows.map((row) => (
            <li
              key={row.title}
              className="flex items-center justify-between gap-4 px-5 py-4 sm:px-7"
            >
              <div>
                <p className="text-sm font-semibold text-slate-900">
                  {row.title}
                </p>
                <p className="mt-0.5 text-xs text-slate-500">
                  {row.description}
                </p>
              </div>
              <StatusBadge tone={row.status.tone}>
                {row.status.label}
              </StatusBadge>
            </li>
          ))}
        </ul>
      </Card>

      <Card>
        <div className="flex items-start gap-3">
          <span
            className={[
              "inline-flex h-9 w-9 shrink-0 items-center justify-center rounded-full",
              noWarnings
                ? "bg-emerald-50 text-emerald-600"
                : "bg-amber-50 text-amber-600",
            ].join(" ")}
          >
            {noWarnings ? <CheckIcon /> : <AlertIcon />}
          </span>
          <div className="flex-1">
            <h3 className="text-sm font-semibold text-slate-900">
              Review warnings
            </h3>

            {analysis.status === "loading" ? (
              <p className="mt-1 text-xs text-slate-400">
                Asking review agents…
              </p>
            ) : null}
            {analysis.status === "error" ? (
              <p className="mt-1 text-xs text-rose-600">
                Backend agent service is offline. Showing local checks only.
              </p>
            ) : null}

            {noWarnings ? (
              <p className="mt-1 text-sm text-slate-600">
                Nothing looks off. You’re ready to prepare your review package.
              </p>
            ) : (
              <div className="mt-2 space-y-3 text-sm text-slate-700">
                {localWarnings.length > 0 ? (
                  <ul className="space-y-1.5">
                    {localWarnings.map((w) => (
                      <li key={w} className="flex gap-2">
                        <span className="mt-1.5 inline-block h-1.5 w-1.5 shrink-0 rounded-full bg-amber-500" />
                        {w}
                      </li>
                    ))}
                  </ul>
                ) : null}

                {apiWarnings.length > 0 ? (
                  <ul className="space-y-1.5">
                    {apiWarnings.map((w) => (
                      <li key={w.code} className="flex gap-2">
                        <SeverityDot severity={w.severity} />
                        <span>
                          <span className="font-medium text-slate-800">
                            {w.code}:
                          </span>{" "}
                          {w.message}
                        </span>
                      </li>
                    ))}
                  </ul>
                ) : null}

                {apiMissing.length > 0 ? (
                  <div>
                    <p className="text-xs font-semibold uppercase tracking-wider text-slate-500">
                      Still needed
                    </p>
                    <ul className="mt-1 space-y-1.5">
                      {apiMissing.map((item) => (
                        <li key={item} className="flex gap-2">
                          <span className="mt-1.5 inline-block h-1.5 w-1.5 shrink-0 rounded-full bg-slate-400" />
                          {item}
                        </li>
                      ))}
                    </ul>
                  </div>
                ) : null}
              </div>
            )}
          </div>
        </div>
      </Card>

      <div className="rounded-2xl border border-slate-200 bg-white px-5 py-4">
        <div className="flex flex-col items-start justify-between gap-3 sm:flex-row sm:items-center">
          <div>
            <h3 className="text-sm font-semibold text-slate-900">
              E-filing integration coming soon
            </h3>
            <p className="mt-1 text-xs text-slate-500">
              In this prototype, you can prepare a review package to share with
              a tax professional.
            </p>
          </div>
          <Button onClick={onPrepare} disabled={prepared}>
            {prepared ? "Review package ready" : "Prepare review package"}
          </Button>
        </div>
      </div>

      {prepared ? (
        <div className="rounded-2xl border border-emerald-200 bg-emerald-50/70 px-4 py-3 text-sm text-emerald-900">
          Your review package has been prepared. A licensed tax professional
          should walk through it with you before any filing.
        </div>
      ) : null}

      <div className="flex items-center justify-between pt-2">
        <Button variant="ghost" onClick={onBack}>
          Back
        </Button>
      </div>
    </div>
  );
}

function SeverityDot({ severity }: { severity: AgentWarningBody["severity"] }) {
  const color =
    severity === "high"
      ? "bg-rose-500"
      : severity === "medium"
        ? "bg-amber-500"
        : severity === "low"
          ? "bg-yellow-400"
          : "bg-slate-400";
  return (
    <span
      className={`mt-1.5 inline-block h-1.5 w-1.5 shrink-0 rounded-full ${color}`}
    />
  );
}

function CheckIcon() {
  return (
    <svg
      width="16"
      height="16"
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth="2.5"
      strokeLinecap="round"
      strokeLinejoin="round"
    >
      <path d="M20 6L9 17l-5-5" />
    </svg>
  );
}
function AlertIcon() {
  return (
    <svg
      width="16"
      height="16"
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth="2"
      strokeLinecap="round"
      strokeLinejoin="round"
    >
      <path d="M12 9v4" />
      <path d="M12 17h.01" />
      <path d="M10.29 3.86L1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z" />
    </svg>
  );
}

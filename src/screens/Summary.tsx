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
import { StatusBadge } from "../components/ui/StatusBadge";
import { useTaxAnalysis } from "../hooks/useTaxAnalysis";
import { buildScenarioRequest } from "../lib/scenarioMapping";
import type { AgentWarningBody } from "../lib/apiTypes";

interface SummaryProps {
  w2: W2Review | null;
  t1098: T1098Review | null;
  manual: ManualEntryData;
  profile: TaxProfile;
  documents: UploadedDocument[];
  taxYear?: number;
  onContinue: () => void;
  onBack: () => void;
}

function parseMoney(input: string): number {
  if (!input) return 0;
  const cleaned = input.replace(/[^0-9.-]/g, "");
  const n = Number(cleaned);
  return Number.isFinite(n) ? n : 0;
}

function formatMoney(n: number): string {
  return n.toLocaleString("en-US", {
    style: "currency",
    currency: "USD",
    maximumFractionDigits: 0,
  });
}

export function Summary({
  w2,
  t1098,
  manual,
  profile,
  documents,
  taxYear = 2025,
  onContinue,
  onBack,
}: SummaryProps) {
  const w2Wages = parseMoney(
    w2?.fields.find((f) => f.id === "wages")?.value ?? manual.w2Wages,
  );
  const fedWithheld = parseMoney(
    w2?.fields.find((f) => f.id === "fedTax")?.value ?? manual.federalWithholding,
  );
  const tuition = parseMoney(
    t1098?.fields.find((f) => f.id === "tuition")?.value ?? manual.educationExpenses,
  );

  const totalIncome = w2Wages;
  const standardDeduction =
    profile.filingStatus === "mfj" || profile.filingStatus === "qss"
      ? 29200
      : profile.filingStatus === "hoh"
        ? 21900
        : 14600;
  const taxableIncome = Math.max(0, totalIncome - standardDeduction);

  const estimatedTax = Math.round(taxableIncome * 0.12);
  const refundOrOwed = fedWithheld - estimatedTax;

  const mayQualifyEducation =
    tuition > 0 &&
    profile.wasStudent === "yes" &&
    profile.canBeClaimedAsDependent !== "yes";

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
        userGoal: "Summarize what is missing or needs review.",
      }),
  });

  return (
    <div className="animate-fade-up mx-auto w-full max-w-3xl space-y-6 px-4 py-8 sm:py-10">
      <SectionHeader
        eyebrow="Step 6"
        title="Your estimated summary"
        description="A quick look at where things stand. This is an estimate — the final review covers everything in detail."
      />

      <Card className="overflow-hidden p-0">
        <div className="bg-gradient-to-br from-slate-900 to-slate-700 px-6 py-7 text-white">
          <p className="text-xs uppercase tracking-wider text-white/60">
            Estimated {refundOrOwed >= 0 ? "refund" : "amount owed"}
          </p>
          <p className="mt-1 text-4xl font-semibold tracking-tight sm:text-5xl">
            {formatMoney(Math.abs(refundOrOwed))}
          </p>
          <p className="mt-2 text-xs text-white/60">
            Estimate only. Final results require full review.
          </p>
        </div>

        <dl className="grid grid-cols-1 divide-y divide-slate-100 sm:grid-cols-2 sm:divide-x sm:divide-y-0">
          <Stat label="Total income" value={formatMoney(totalIncome)} />
          <Stat
            label="Federal tax withheld"
            value={formatMoney(fedWithheld)}
          />
          <Stat
            label="Standard deduction"
            value={formatMoney(standardDeduction)}
          />
          <Stat
            label="Estimated taxable income"
            value={formatMoney(taxableIncome)}
          />
        </dl>
      </Card>

      <Card>
        <div className="flex items-start justify-between gap-4">
          <div>
            <h3 className="text-sm font-semibold text-slate-900">
              Education credit review
            </h3>
            <p className="mt-1 max-w-xl text-sm text-slate-600">
              {mayQualifyEducation
                ? "Based on your answers, you may be eligible for an education credit. Please review the requirement checklist before deciding."
                : "Education credits don’t appear to apply based on your current answers. You can revisit this in the final review."}
            </p>
          </div>
          <StatusBadge tone={mayQualifyEducation ? "info" : "neutral"}>
            {mayQualifyEducation ? "May apply" : "Not applicable"}
          </StatusBadge>
        </div>
      </Card>

      <AgentInsightsCard analysis={analysis} />

      <div className="rounded-2xl border border-amber-200 bg-amber-50/70 px-4 py-3 text-xs text-amber-900">
        TaxMax AI provides AI-assisted preparation support. It does not provide
        legal or tax advice. Numbers shown are estimates for prototype purposes.
      </div>

      <div className="flex items-center justify-between pt-2">
        <Button variant="ghost" onClick={onBack}>
          Back
        </Button>
        <Button onClick={onContinue}>Go to final review</Button>
      </div>
    </div>
  );
}

function AgentInsightsCard({
  analysis,
}: {
  analysis: ReturnType<typeof useTaxAnalysis>;
}) {
  return (
    <Card>
      <div className="flex items-center justify-between gap-4">
        <h3 className="text-sm font-semibold text-slate-900">Agent insights</h3>
        <StatusBadge tone={toneForAnalysis(analysis)}>
          {labelForAnalysis(analysis)}
        </StatusBadge>
      </div>

      {analysis.status === "loading" ? (
        <p className="mt-3 text-sm text-slate-500">
          Asking the TaxMax review agents to look at your scenario…
        </p>
      ) : null}

      {analysis.status === "error" ? (
        <p className="mt-3 text-sm text-rose-700">
          Couldn’t reach the review service. Start the backend (uvicorn on port
          8000) and revisit this step.
        </p>
      ) : null}

      {analysis.status === "success" ? (
        <AgentInsightsBody data={analysis.data} />
      ) : null}
    </Card>
  );
}

function AgentInsightsBody({
  data,
}: {
  data: ReturnType<typeof useTaxAnalysis> extends infer T
    ? T extends { status: "success"; data: infer D }
      ? D
      : never
    : never;
}) {
  const hasContent =
    data.findings.length > 0 ||
    data.warnings.length > 0 ||
    data.missing_information.length > 0 ||
    data.next_questions.length > 0;

  if (!hasContent) {
    return (
      <p className="mt-3 text-sm text-slate-500">
        Nothing flagged yet. The agents will surface findings as you add
        information.
      </p>
    );
  }

  return (
    <div className="mt-4 space-y-4 text-sm text-slate-700">
      {data.missing_information.length > 0 ? (
        <div>
          <p className="text-xs font-semibold uppercase tracking-wider text-slate-500">
            Still needed
          </p>
          <ul className="mt-1 space-y-1">
            {data.missing_information.map((item) => (
              <li key={item} className="flex gap-2">
                <span className="mt-1.5 inline-block h-1.5 w-1.5 shrink-0 rounded-full bg-slate-400" />
                {item}
              </li>
            ))}
          </ul>
        </div>
      ) : null}

      {data.next_questions.length > 0 ? (
        <div>
          <p className="text-xs font-semibold uppercase tracking-wider text-slate-500">
            Suggested next questions
          </p>
          <ul className="mt-1 space-y-1">
            {data.next_questions.map((q) => (
              <li key={q} className="flex gap-2">
                <span className="mt-1.5 inline-block h-1.5 w-1.5 shrink-0 rounded-full bg-blue-500" />
                {q}
              </li>
            ))}
          </ul>
        </div>
      ) : null}

      {data.warnings.length > 0 ? (
        <div>
          <p className="text-xs font-semibold uppercase tracking-wider text-slate-500">
            Warnings
          </p>
          <ul className="mt-1 space-y-1">
            {data.warnings.map((w) => (
              <li key={w.code} className="flex gap-2">
                <SeverityDot severity={w.severity} />
                <span>
                  <span className="font-medium text-slate-800">{w.code}:</span>{" "}
                  {w.message}
                </span>
              </li>
            ))}
          </ul>
        </div>
      ) : null}

      {data.findings.length > 0 ? (
        <div>
          <p className="text-xs font-semibold uppercase tracking-wider text-slate-500">
            Findings
          </p>
          <ul className="mt-1 space-y-2">
            {data.findings.map((f, idx) => (
              <li key={`${f.agent_name}-${idx}`} className="rounded-xl bg-slate-50 px-3 py-2">
                <p className="text-xs font-medium text-slate-500">
                  {f.agent_name} · {f.category}
                </p>
                <p className="mt-1 text-sm text-slate-800">{f.summary}</p>
                {f.suggested_action ? (
                  <p className="mt-1 text-xs text-slate-500">
                    Next: {f.suggested_action}
                  </p>
                ) : null}
              </li>
            ))}
          </ul>
        </div>
      ) : null}
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

function toneForAnalysis(
  analysis: ReturnType<typeof useTaxAnalysis>,
): "info" | "neutral" | "complete" | "missing" | "review" {
  if (analysis.status !== "success") return "neutral";
  switch (analysis.data.status) {
    case "needs_more_information":
      return "missing";
    case "review_required":
      return "review";
    case "draft":
      return "complete";
    default:
      return "neutral";
  }
}

function labelForAnalysis(
  analysis: ReturnType<typeof useTaxAnalysis>,
): string {
  if (analysis.status === "loading") return "Reviewing…";
  if (analysis.status === "error") return "Offline";
  if (analysis.status === "idle") return "Idle";
  switch (analysis.data.status) {
    case "needs_more_information":
      return "More info needed";
    case "review_required":
      return "Review required";
    case "draft":
      return "Looks reasonable";
    case "error":
      return "Error";
    default:
      return "—";
  }
}

function Stat({ label, value }: { label: string; value: string }) {
  return (
    <div className="px-6 py-4">
      <dt className="text-xs uppercase tracking-wider text-slate-400">{label}</dt>
      <dd className="mt-1 text-lg font-semibold text-slate-900">{value}</dd>
    </div>
  );
}

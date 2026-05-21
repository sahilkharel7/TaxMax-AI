import { useMemo, type ReactNode } from "react";
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
import { useTaxOptimization } from "../hooks/useTaxOptimization";
import { buildScenarioRequest } from "../lib/scenarioMapping";
import { isBackendEnabled } from "../lib/api";
import type { AgentWarningBody, TaxSavingsOpportunityBody } from "../lib/apiTypes";

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
  const optimization = useTaxOptimization({
    cacheKey: scenarioCacheKey,
    buildScenario: () =>
      buildScenarioRequest({
        profile,
        manual,
        w2,
        t1098,
        documents,
        taxYear,
        userGoal: "Find potential legal tax-saving opportunities before filing.",
      }),
  });
  const backendMode = isBackendEnabled();

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

      <AgentInsightsCard analysis={analysis} backendMode={backendMode} />

      <SavingsOpportunitiesCard optimization={optimization} />

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

function SavingsOpportunitiesCard({
  optimization,
}: {
  optimization: ReturnType<typeof useTaxOptimization>;
}) {
  return (
    <Card>
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div>
          <h3 className="text-sm font-semibold text-slate-900">
            Tax savings opportunities
          </h3>
          <p className="mt-1 text-xs text-slate-500">
            Legal deduction, credit, filing status, state, and documentation review areas.
          </p>
        </div>
        <StatusBadge tone={toneForOptimization(optimization)}>
          {labelForOptimization(optimization)}
        </StatusBadge>
      </div>

      {optimization.status === "loading" ? (
        <div className="mt-4 rounded-2xl border border-slate-200 bg-slate-50 px-4 py-4 text-sm text-slate-600">
          Looking for potential legal tax-saving review areas...
        </div>
      ) : null}

      {optimization.status === "error" ? (
        <div className="mt-4 rounded-2xl border border-rose-200 bg-rose-50 px-4 py-4 text-sm text-rose-700">
          The savings review service could not be reached. You can still continue with the basic summary.
        </div>
      ) : null}

      {optimization.status === "success" ? (
        <div className="mt-4 space-y-3">
          <p className="rounded-2xl border border-slate-200 bg-slate-50 px-4 py-3 text-sm text-slate-600">
            {optimization.data.review_package_summary}
          </p>
          {optimization.data.opportunities.slice(0, 4).map((opportunity) => (
            <OpportunityCard
              key={opportunity.opportunity_id}
              opportunity={opportunity}
            />
          ))}
          {optimization.data.missing_information.length > 0 ? (
            <div className="rounded-2xl border border-amber-200 bg-amber-50/70 px-4 py-3">
              <p className="text-xs font-semibold uppercase tracking-wider text-amber-800">
                Needed for better review
              </p>
              <div className="mt-2 flex flex-wrap gap-2">
                {optimization.data.missing_information.map((item) => (
                  <span
                    key={item}
                    className="rounded-full bg-white px-2.5 py-1 text-xs text-amber-900 ring-1 ring-amber-200"
                  >
                    {item}
                  </span>
                ))}
              </div>
            </div>
          ) : null}
        </div>
      ) : null}
    </Card>
  );
}

function OpportunityCard({
  opportunity,
}: {
  opportunity: TaxSavingsOpportunityBody;
}) {
  return (
    <div className="rounded-2xl border border-slate-200 bg-white p-4">
      <div className="flex flex-wrap items-start justify-between gap-3">
        <div>
          <p className="text-[11px] font-semibold uppercase tracking-wider text-slate-400">
            {opportunity.agent_name} · {opportunity.category.replace(/_/g, " ")}
          </p>
          <h4 className="mt-1 text-sm font-semibold text-slate-900">
            {opportunity.title}
          </h4>
        </div>
        <div className="flex gap-2">
          <StatusBadge tone={toneForImpact(opportunity.potential_impact)}>
            {opportunity.potential_impact} impact
          </StatusBadge>
          <StatusBadge tone={toneForRisk(opportunity.risk_level)}>
            {opportunity.risk_level} risk
          </StatusBadge>
        </div>
      </div>
      <p className="mt-3 text-sm text-slate-700">{opportunity.summary}</p>
      {opportunity.estimated_directional_effect ? (
        <p className="mt-2 text-xs text-slate-500">
          Direction: {opportunity.estimated_directional_effect}
        </p>
      ) : null}
      <div className="mt-3 grid gap-3 sm:grid-cols-2">
        <MiniList title="Facts to confirm" items={opportunity.required_facts} />
        <MiniList title="Documents" items={opportunity.required_documents} />
      </div>
      <p className="mt-3 text-xs text-slate-500">
        Next: {opportunity.suggested_next_step}
      </p>
    </div>
  );
}

function MiniList({ title, items }: { title: string; items: string[] }) {
  return (
    <div className="rounded-xl border border-slate-200 bg-slate-50/70 px-3 py-3">
      <p className="text-[11px] font-semibold uppercase tracking-wider text-slate-500">
        {title}
      </p>
      {items.length > 0 ? (
        <ul className="mt-2 space-y-1 text-xs text-slate-600">
          {items.slice(0, 3).map((item) => (
            <li key={item}>- {item}</li>
          ))}
        </ul>
      ) : (
        <p className="mt-2 text-xs text-slate-400">None listed</p>
      )}
    </div>
  );
}

function AgentInsightsCard({
  analysis,
  backendMode,
}: {
  analysis: ReturnType<typeof useTaxAnalysis>;
  backendMode: boolean;
}) {
  return (
    <Card>
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div>
          <h3 className="text-sm font-semibold text-slate-900">
            Agent insights
          </h3>
          <p className="mt-1 text-xs text-slate-500">
            {backendMode
              ? "Live backend mode is enabled for this summary."
              : "Mock mode is enabled so you can keep using the app without the backend."}
          </p>
        </div>
        <StatusBadge tone={toneForAnalysis(analysis)}>
          {labelForAnalysis(analysis)}
        </StatusBadge>
      </div>

      {analysis.status === "loading" ? (
        <div className="mt-4 rounded-2xl border border-slate-200 bg-slate-50 px-4 py-4 text-sm text-slate-600">
          Reviewing your scenario and preparing a plain-language summary…
        </div>
      ) : null}

      {analysis.status === "error" ? (
        <div className="mt-4 rounded-2xl border border-rose-200 bg-rose-50 px-4 py-4 text-sm text-rose-700">
          The backend review service could not be reached. The rest of the
          summary remains available.
        </div>
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
      <div className="mt-4 rounded-2xl border border-slate-200 bg-slate-50 px-4 py-4 text-sm text-slate-600">
        Nothing flagged yet. The review agents will surface items as you add
        information.
      </div>
    );
  }

  return (
    <div className="mt-4 grid gap-4 lg:grid-cols-2">
      <AnalysisSectionCard title="Findings" emptyLabel="No findings yet">
        {data.findings.map((finding, idx) => (
          <div
            key={`${finding.agent_name}-${finding.category}-${idx}`}
            className="rounded-xl border border-slate-200 bg-white p-3"
          >
            <div className="flex flex-wrap items-center justify-between gap-2">
              <p className="text-xs font-semibold text-slate-500">
                {finding.agent_name} · {finding.category}
              </p>
              <StatusBadge tone="info">{finding.confidence}</StatusBadge>
            </div>
            <p className="mt-2 text-sm text-slate-800">{finding.summary}</p>
            {finding.suggested_action ? (
              <p className="mt-2 text-xs text-slate-500">
                Next: {finding.suggested_action}
              </p>
            ) : null}
          </div>
        ))}
      </AnalysisSectionCard>

      <AnalysisSectionCard title="Warnings" emptyLabel="No warnings yet">
        {data.warnings.map((warning) => (
          <div
            key={warning.code}
            className="rounded-xl border border-slate-200 bg-white p-3"
          >
            <div className="flex flex-wrap items-center justify-between gap-2">
              <p className="text-xs font-semibold text-slate-500">
                {warning.code}
              </p>
              <StatusBadge tone={toneForSeverity(warning.severity)}>
                {warning.severity}
              </StatusBadge>
            </div>
            <p className="mt-2 text-sm text-slate-800">{warning.message}</p>
            {warning.recommended_follow_up ? (
              <p className="mt-2 text-xs text-slate-500">
                Follow-up: {warning.recommended_follow_up}
              </p>
            ) : null}
          </div>
        ))}
      </AnalysisSectionCard>

      <AnalysisSectionCard
        title="Missing information"
        emptyLabel="No missing information"
      >
        {data.missing_information.map((item) => (
          <div
            key={item}
            className="rounded-xl border border-slate-200 bg-white px-3 py-2 text-sm text-slate-700"
          >
            {item}
          </div>
        ))}
      </AnalysisSectionCard>

      <AnalysisSectionCard
        title="Next questions"
        emptyLabel="No follow-up questions"
      >
        {data.next_questions.map((question) => (
          <div
            key={question}
            className="rounded-xl border border-slate-200 bg-white px-3 py-2 text-sm text-slate-700"
          >
            {question}
          </div>
        ))}
      </AnalysisSectionCard>
    </div>
  );
}

function AnalysisSectionCard({
  title,
  emptyLabel,
  children,
}: {
  title: string;
  emptyLabel: string;
  children: ReactNode;
}) {
  const childArray = Array.isArray(children) ? children : [children];
  const hasItems = childArray.some(Boolean);

  return (
    <div className="rounded-2xl border border-slate-200 bg-slate-50/70 p-4">
      <p className="text-xs font-semibold uppercase tracking-wider text-slate-500">
        {title}
      </p>
      <div className="mt-3 space-y-3">
        {hasItems ? (
          children
        ) : (
          <div className="rounded-xl border border-dashed border-slate-200 bg-white px-3 py-3 text-sm text-slate-500">
            {emptyLabel}
          </div>
        )}
      </div>
    </div>
  );
}

function toneForSeverity(
  severity: AgentWarningBody["severity"],
): "complete" | "review" | "missing" | "info" | "neutral" {
  if (severity === "high") return "missing";
  if (severity === "medium") return "review";
  if (severity === "low") return "info";
  return "neutral";
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

function toneForOptimization(
  optimization: ReturnType<typeof useTaxOptimization>,
): "info" | "neutral" | "complete" | "missing" | "review" {
  if (optimization.status !== "success") return "neutral";
  switch (optimization.data.status) {
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

function labelForOptimization(
  optimization: ReturnType<typeof useTaxOptimization>,
): string {
  if (optimization.status === "loading") return "Scanning...";
  if (optimization.status === "error") return "Offline";
  if (optimization.status === "idle") return "Idle";
  switch (optimization.data.status) {
    case "needs_more_information":
      return "More info needed";
    case "review_required":
      return "Review found";
    case "draft":
      return "Ready";
    case "error":
      return "Error";
    default:
      return "-";
  }
}

function toneForImpact(
  impact: TaxSavingsOpportunityBody["potential_impact"],
): "info" | "neutral" | "complete" | "missing" | "review" {
  if (impact === "high") return "complete";
  if (impact === "medium") return "info";
  if (impact === "low") return "neutral";
  return "review";
}

function toneForRisk(
  risk: TaxSavingsOpportunityBody["risk_level"],
): "info" | "neutral" | "complete" | "missing" | "review" {
  if (risk === "high") return "missing";
  if (risk === "medium") return "review";
  if (risk === "low") return "complete";
  return "neutral";
}

function Stat({ label, value }: { label: string; value: string }) {
  return (
    <div className="px-6 py-4">
      <dt className="text-xs uppercase tracking-wider text-slate-400">{label}</dt>
      <dd className="mt-1 text-lg font-semibold text-slate-900">{value}</dd>
    </div>
  );
}

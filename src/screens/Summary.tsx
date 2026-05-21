import type {
  ManualEntryData,
  T1098Review,
  TaxProfile,
  W2Review,
} from "../types";
import { Button } from "../components/ui/Button";
import { Card, SectionHeader } from "../components/ui/Card";
import { StatusBadge } from "../components/ui/StatusBadge";

interface SummaryProps {
  w2: W2Review | null;
  t1098: T1098Review | null;
  manual: ManualEntryData;
  profile: TaxProfile;
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
  // Mock 2024 single standard deduction; this is illustrative only.
  const standardDeduction =
    profile.filingStatus === "mfj" || profile.filingStatus === "qss"
      ? 29200
      : profile.filingStatus === "hoh"
        ? 21900
        : 14600;
  const taxableIncome = Math.max(0, totalIncome - standardDeduction);

  // Extremely rough mock effective rate, prototype only.
  const estimatedTax = Math.round(taxableIncome * 0.12);
  const refundOrOwed = fedWithheld - estimatedTax;

  const mayQualifyEducation =
    tuition > 0 &&
    profile.wasStudent === "yes" &&
    profile.canBeClaimedAsDependent !== "yes";

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

function Stat({ label, value }: { label: string; value: string }) {
  return (
    <div className="px-6 py-4">
      <dt className="text-xs uppercase tracking-wider text-slate-400">{label}</dt>
      <dd className="mt-1 text-lg font-semibold text-slate-900">{value}</dd>
    </div>
  );
}

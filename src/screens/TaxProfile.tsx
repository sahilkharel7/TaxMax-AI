import type { FilingStatus, TaxProfile as TaxProfileT, YesNo } from "../types";
import { Button } from "../components/ui/Button";
import { Card, SectionHeader } from "../components/ui/Card";
import { ChoiceCard } from "../components/ui/ChoiceCard";

interface TaxProfileProps {
  profile: TaxProfileT;
  onChange: (next: TaxProfileT) => void;
  onContinue: () => void;
  onBack: () => void;
}

const FILING: { id: FilingStatus; label: string; description: string }[] = [
  {
    id: "single",
    label: "Single",
    description: "Unmarried, not eligible for another status.",
  },
  {
    id: "mfj",
    label: "Married filing jointly",
    description: "Married, combining incomes on one return.",
  },
  {
    id: "mfs",
    label: "Married filing separately",
    description: "Married, but each spouse files individually.",
  },
  {
    id: "hoh",
    label: "Head of household",
    description: "Unmarried and paid more than half a home’s costs.",
  },
  {
    id: "qss",
    label: "Qualifying surviving spouse",
    description: "Spouse died in the past 2 years and you have a child.",
  },
];

interface YesNoQuestion {
  id: keyof Omit<TaxProfileT, "filingStatus">;
  question: string;
}

const QUESTIONS: YesNoQuestion[] = [
  { id: "canBeClaimedAsDependent", question: "Can someone else claim you as a dependent?" },
  { id: "wasStudent", question: "Were you a student this year?" },
  { id: "received1098T", question: "Did you receive a 1098-T?" },
  { id: "multipleJobs", question: "Did you have more than one job?" },
  { id: "received1099", question: "Did you receive any 1099 forms?" },
];

export function TaxProfile({
  profile,
  onChange,
  onContinue,
  onBack,
}: TaxProfileProps) {
  const answeredAll =
    profile.filingStatus !== null &&
    QUESTIONS.every((q) => profile[q.id] !== null);

  const set = <K extends keyof TaxProfileT>(key: K, value: TaxProfileT[K]) =>
    onChange({ ...profile, [key]: value });

  return (
    <div className="animate-fade-up mx-auto w-full max-w-3xl space-y-6 px-4 py-8 sm:py-10">
      <SectionHeader
        eyebrow="Step 5"
        title="A few quick questions"
        description="Your answers shape the rest of the flow. Be honest — TaxMax AI guides, it doesn’t decide."
      />

      <Card>
        <h3 className="text-sm font-semibold text-slate-900">
          What’s your filing status?
        </h3>
        <div className="mt-4 grid grid-cols-1 gap-2 sm:grid-cols-2">
          {FILING.map((opt) => (
            <ChoiceCard
              key={opt.id ?? "none"}
              selected={profile.filingStatus === opt.id}
              onClick={() => set("filingStatus", opt.id)}
              title={opt.label}
              description={opt.description}
            />
          ))}
        </div>
      </Card>

      {QUESTIONS.map((q) => (
        <Card key={q.id}>
          <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
            <h3 className="text-sm font-medium text-slate-900">{q.question}</h3>
            <YesNoPicker
              value={profile[q.id] as YesNo}
              onChange={(v) => set(q.id, v)}
            />
          </div>
        </Card>
      ))}

      <div className="flex items-center justify-between pt-2">
        <Button variant="ghost" onClick={onBack}>
          Back
        </Button>
        <Button onClick={onContinue} disabled={!answeredAll}>
          See summary
        </Button>
      </div>
    </div>
  );
}

function YesNoPicker({
  value,
  onChange,
}: {
  value: YesNo;
  onChange: (v: YesNo) => void;
}) {
  const opt = (v: "yes" | "no", label: string) => (
    <button
      key={v}
      type="button"
      onClick={() => onChange(v)}
      className={[
        "h-10 min-w-[80px] rounded-full px-4 text-sm font-medium transition",
        value === v
          ? "bg-slate-900 text-white"
          : "bg-white text-slate-700 ring-1 ring-inset ring-slate-200 hover:bg-slate-50",
      ].join(" ")}
    >
      {label}
    </button>
  );
  return (
    <div className="flex shrink-0 gap-2">
      {opt("yes", "Yes")}
      {opt("no", "No")}
    </div>
  );
}

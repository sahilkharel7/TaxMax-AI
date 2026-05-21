import type { ManualEntryData, FilingStatus, YesNo } from "../types";
import { Button } from "../components/ui/Button";
import { Card, SectionHeader } from "../components/ui/Card";
import { Field, Input, Select } from "../components/ui/Input";
import { ChoiceCard } from "../components/ui/ChoiceCard";

interface ManualEntryProps {
  data: ManualEntryData;
  onChange: (next: ManualEntryData) => void;
  onContinue: () => void;
  onBack: () => void;
}

const FILING_OPTIONS: { id: FilingStatus; label: string }[] = [
  { id: "single", label: "Single" },
  { id: "mfj", label: "Married filing jointly" },
  { id: "mfs", label: "Married filing separately" },
  { id: "hoh", label: "Head of household" },
  { id: "qss", label: "Qualifying surviving spouse" },
];

export function ManualEntry({
  data,
  onChange,
  onContinue,
  onBack,
}: ManualEntryProps) {
  const setPersonal = (key: keyof ManualEntryData["personal"], value: string) =>
    onChange({ ...data, personal: { ...data.personal, [key]: value } });

  const setField = <K extends keyof ManualEntryData>(
    key: K,
    value: ManualEntryData[K],
  ) => onChange({ ...data, [key]: value });

  const setCredit = (
    key: keyof ManualEntryData["credits"],
    value: boolean,
  ) => onChange({ ...data, credits: { ...data.credits, [key]: value } });

  return (
    <div className="animate-fade-up mx-auto w-full max-w-3xl space-y-6 px-4 py-8 sm:py-10">
      <SectionHeader
        eyebrow="Step 3"
        title="Tell us about you"
        description="Enter the information you have on hand. You can edit anything before the final review."
      />

      <Card>
        <h3 className="text-sm font-semibold text-slate-900">
          Personal information
        </h3>
        <div className="mt-4 grid grid-cols-1 gap-4 sm:grid-cols-2">
          <Field label="First name" required>
            <Input
              value={data.personal.firstName}
              onChange={(e) => setPersonal("firstName", e.target.value)}
              placeholder="Jane"
            />
          </Field>
          <Field label="Last name" required>
            <Input
              value={data.personal.lastName}
              onChange={(e) => setPersonal("lastName", e.target.value)}
              placeholder="Doe"
            />
          </Field>
          <Field label="Social Security Number" hint="Stored only in this session">
            <Input
              value={data.personal.ssn}
              onChange={(e) => setPersonal("ssn", e.target.value)}
              placeholder="•••-••-••••"
              inputMode="numeric"
            />
          </Field>
          <Field label="Date of birth">
            <Input
              type="date"
              value={data.personal.dateOfBirth}
              onChange={(e) => setPersonal("dateOfBirth", e.target.value)}
            />
          </Field>
          <Field label="Email">
            <Input
              type="email"
              value={data.personal.email}
              onChange={(e) => setPersonal("email", e.target.value)}
              placeholder="jane@example.com"
            />
          </Field>
          <Field label="Address">
            <Input
              value={data.personal.address}
              onChange={(e) => setPersonal("address", e.target.value)}
              placeholder="Street address"
            />
          </Field>
          <Field label="City">
            <Input
              value={data.personal.city}
              onChange={(e) => setPersonal("city", e.target.value)}
            />
          </Field>
          <div className="grid grid-cols-2 gap-3">
            <Field label="State">
              <Input
                value={data.personal.state}
                onChange={(e) => setPersonal("state", e.target.value)}
                placeholder="NY"
                maxLength={2}
              />
            </Field>
            <Field label="ZIP">
              <Input
                value={data.personal.zip}
                onChange={(e) => setPersonal("zip", e.target.value)}
                placeholder="10027"
                inputMode="numeric"
              />
            </Field>
          </div>
        </div>
      </Card>

      <Card>
        <h3 className="text-sm font-semibold text-slate-900">Filing status</h3>
        <p className="mt-1 text-xs text-slate-500">
          How are you filing this year?
        </p>
        <div className="mt-4 grid grid-cols-1 gap-2 sm:grid-cols-2">
          {FILING_OPTIONS.map((opt) => (
            <ChoiceCard
              key={opt.id ?? "none"}
              selected={data.filingStatus === opt.id}
              onClick={() => setField("filingStatus", opt.id)}
              title={opt.label}
              compact
            />
          ))}
        </div>
      </Card>

      <Card>
        <h3 className="text-sm font-semibold text-slate-900">Income</h3>
        <div className="mt-4 grid grid-cols-1 gap-4 sm:grid-cols-2">
          <Field label="W-2 wages (Box 1)">
            <Input
              value={data.w2Wages}
              onChange={(e) => setField("w2Wages", e.target.value)}
              placeholder="$0.00"
              inputMode="decimal"
            />
          </Field>
          <Field label="Federal income tax withheld (Box 2)">
            <Input
              value={data.federalWithholding}
              onChange={(e) => setField("federalWithholding", e.target.value)}
              placeholder="$0.00"
              inputMode="decimal"
            />
          </Field>
        </div>
      </Card>

      <Card>
        <h3 className="text-sm font-semibold text-slate-900">Education</h3>
        <div className="mt-4 grid grid-cols-1 gap-4 sm:grid-cols-2">
          <Field label="Qualified education expenses">
            <Input
              value={data.educationExpenses}
              onChange={(e) => setField("educationExpenses", e.target.value)}
              placeholder="$0.00"
              inputMode="decimal"
            />
          </Field>
          <Field label="Were you a student this year?">
            <Select
              value={data.isStudent ?? ""}
              onChange={(e) =>
                setField("isStudent", (e.target.value || null) as YesNo)
              }
            >
              <option value="">Select…</option>
              <option value="yes">Yes</option>
              <option value="no">No</option>
            </Select>
          </Field>
        </div>
      </Card>

      <Card>
        <h3 className="text-sm font-semibold text-slate-900">
          Credits checklist
        </h3>
        <p className="mt-1 text-xs text-slate-500">
          Check any that may apply. We’ll surface them in the final review.
        </p>
        <div className="mt-4 grid grid-cols-1 gap-2 sm:grid-cols-2">
          <CreditToggle
            label="Earned Income Tax Credit (EITC)"
            checked={data.credits.earnedIncomeCredit}
            onChange={(v) => setCredit("earnedIncomeCredit", v)}
          />
          <CreditToggle
            label="Child Tax Credit"
            checked={data.credits.childTaxCredit}
            onChange={(v) => setCredit("childTaxCredit", v)}
          />
          <CreditToggle
            label="Education credit (AOTC / LLC)"
            checked={data.credits.educationCredit}
            onChange={(v) => setCredit("educationCredit", v)}
          />
          <CreditToggle
            label="Saver’s Credit"
            checked={data.credits.savingsContributionsCredit}
            onChange={(v) => setCredit("savingsContributionsCredit", v)}
          />
        </div>
      </Card>

      <div className="flex items-center justify-between pt-2">
        <Button variant="ghost" onClick={onBack}>
          Back
        </Button>
        <Button onClick={onContinue}>Continue</Button>
      </div>
    </div>
  );
}

function CreditToggle({
  label,
  checked,
  onChange,
}: {
  label: string;
  checked: boolean;
  onChange: (v: boolean) => void;
}) {
  return (
    <label
      className={[
        "flex cursor-pointer items-center gap-3 rounded-2xl border bg-white px-4 py-3 transition",
        checked
          ? "border-slate-900 ring-2 ring-slate-900/5"
          : "border-slate-200 hover:border-slate-300",
      ].join(" ")}
    >
      <span
        className={[
          "flex h-5 w-5 items-center justify-center rounded-md border transition",
          checked
            ? "border-slate-900 bg-slate-900 text-white"
            : "border-slate-300",
        ].join(" ")}
      >
        {checked ? (
          <svg
            width="12"
            height="12"
            viewBox="0 0 24 24"
            fill="none"
            stroke="currentColor"
            strokeWidth="3"
            strokeLinecap="round"
            strokeLinejoin="round"
          >
            <path d="M20 6L9 17l-5-5" />
          </svg>
        ) : null}
      </span>
      <span className="text-sm text-slate-800">{label}</span>
      <input
        type="checkbox"
        className="sr-only"
        checked={checked}
        onChange={(e) => onChange(e.target.checked)}
      />
    </label>
  );
}

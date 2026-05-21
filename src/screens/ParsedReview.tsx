import { useMemo, useState } from "react";
import type { ReviewField, T1098Review, W2Review } from "../types";
import { Button } from "../components/ui/Button";
import { Card, SectionHeader } from "../components/ui/Card";
import { StatusBadge } from "../components/ui/StatusBadge";
import { Input } from "../components/ui/Input";

interface ParsedReviewProps {
  w2: W2Review | null;
  t1098: T1098Review | null;
  onUpdateW2: (next: W2Review) => void;
  onUpdate1098T: (next: T1098Review) => void;
  onContinue: () => void;
  onBack: () => void;
}

export function ParsedReview({
  w2,
  t1098,
  onUpdateW2,
  onUpdate1098T,
  onContinue,
  onBack,
}: ParsedReviewProps) {
  const totalFields = (w2?.fields.length ?? 0) + (t1098?.fields.length ?? 0);
  const confirmedCount =
    (w2?.fields.filter((f) => f.confirmed).length ?? 0) +
    (t1098?.fields.filter((f) => f.confirmed).length ?? 0);
  const canContinue = totalFields > 0 && confirmedCount === totalFields;

  return (
    <div className="animate-fade-up mx-auto w-full max-w-3xl space-y-6 px-4 py-8 sm:py-10">
      <SectionHeader
        eyebrow="Step 4"
        title="Review extracted data"
        description="We pulled these values from your uploads. Confirm each one matches your original document before moving on."
      />

      <div className="rounded-2xl border border-blue-100 bg-blue-50/60 px-4 py-3 text-sm text-blue-900">
        <p className="font-medium">Quick check</p>
        <p className="mt-0.5 text-blue-800/80">
          {confirmedCount} of {totalFields} fields confirmed. Document parsing
          may contain errors — your eyes are the source of truth.
        </p>
      </div>

      {w2 ? (
        <ReviewBlock
          title="W-2"
          subtitle="Wage and tax statement"
          review={w2}
          onUpdate={onUpdateW2}
        />
      ) : null}

      {t1098 ? (
        <ReviewBlock
          title="1098-T"
          subtitle="Tuition statement"
          review={t1098}
          onUpdate={onUpdate1098T}
        />
      ) : null}

      {!w2 && !t1098 ? (
        <Card>
          <p className="text-sm text-slate-600">
            No documents were parsed in this session. Go back and upload a W-2
            or 1098-T to continue.
          </p>
        </Card>
      ) : null}

      <div className="flex items-center justify-between pt-2">
        <Button variant="ghost" onClick={onBack}>
          Back
        </Button>
        <Button onClick={onContinue} disabled={!canContinue}>
          Confirm and continue
        </Button>
      </div>
    </div>
  );
}

interface ReviewBlockProps<T extends W2Review | T1098Review> {
  title: string;
  subtitle: string;
  review: T;
  onUpdate: (next: T) => void;
}

function ReviewBlock<T extends W2Review | T1098Review>({
  title,
  subtitle,
  review,
  onUpdate,
}: ReviewBlockProps<T>) {
  const allConfirmed = review.fields.every((f) => f.confirmed);
  const partial =
    !allConfirmed && review.fields.some((f) => f.confirmed);

  const updateField = (next: ReviewField) => {
    onUpdate({
      ...review,
      fields: review.fields.map((f) => (f.id === next.id ? next : f)),
    } as T);
  };

  return (
    <Card>
      <div className="mb-4 flex items-center justify-between">
        <div>
          <p className="text-[11px] font-semibold uppercase tracking-wider text-slate-400">
            {subtitle}
          </p>
          <h3 className="text-lg font-semibold text-slate-900">{title}</h3>
        </div>
        <StatusBadge
          tone={allConfirmed ? "complete" : partial ? "review" : "info"}
        >
          {allConfirmed
            ? "All confirmed"
            : partial
              ? "In progress"
              : "Needs review"}
        </StatusBadge>
      </div>
      <ul className="divide-y divide-slate-100">
        {review.fields.map((field) => (
          <ReviewRow key={field.id} field={field} onUpdate={updateField} />
        ))}
      </ul>
    </Card>
  );
}

interface ReviewRowProps {
  field: ReviewField;
  onUpdate: (next: ReviewField) => void;
}

function ReviewRow({ field, onUpdate }: ReviewRowProps) {
  const [editing, setEditing] = useState(false);
  const [draft, setDraft] = useState(field.value);

  const save = () => {
    onUpdate({ ...field, value: draft, confirmed: true });
    setEditing(false);
  };

  const toggleConfirm = () =>
    onUpdate({ ...field, confirmed: !field.confirmed });

  const sourceTag = useMemo(() => field.source, [field.source]);

  return (
    <li className="grid grid-cols-1 gap-3 py-4 first:pt-0 last:pb-0 sm:grid-cols-[1fr_auto] sm:items-center">
      <div>
        <p className="text-xs font-medium uppercase tracking-wide text-slate-400">
          {sourceTag}
        </p>
        <p className="mt-0.5 text-sm font-medium text-slate-900">
          {field.label}
        </p>
        {editing ? (
          <div className="mt-2 flex gap-2">
            <Input
              value={draft}
              onChange={(e) => setDraft(e.target.value)}
              className="h-9 max-w-xs text-sm"
              autoFocus
            />
            <Button size="sm" onClick={save}>
              Save
            </Button>
            <Button
              size="sm"
              variant="ghost"
              onClick={() => {
                setDraft(field.value);
                setEditing(false);
              }}
            >
              Cancel
            </Button>
          </div>
        ) : (
          <p className="mt-1 text-base text-slate-700">{field.value}</p>
        )}
      </div>

      <div className="flex items-center gap-2 sm:justify-end">
        {!editing ? (
          <Button
            size="sm"
            variant="ghost"
            onClick={() => {
              setDraft(field.value);
              setEditing(true);
            }}
          >
            Edit
          </Button>
        ) : null}
        <label
          className={[
            "inline-flex cursor-pointer select-none items-center gap-2 rounded-full px-3 py-1.5 text-xs font-medium ring-1 ring-inset transition",
            field.confirmed
              ? "bg-emerald-50 text-emerald-700 ring-emerald-200"
              : "bg-white text-slate-600 ring-slate-200 hover:bg-slate-50",
          ].join(" ")}
        >
          <input
            type="checkbox"
            className="sr-only"
            checked={field.confirmed}
            onChange={toggleConfirm}
          />
          {field.confirmed ? (
            <>
              <CheckIcon />
              Confirmed
            </>
          ) : (
            "Mark as correct"
          )}
        </label>
      </div>
    </li>
  );
}

function CheckIcon() {
  return (
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
  );
}

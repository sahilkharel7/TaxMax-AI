import type { ReactNode } from "react";

interface ChoiceCardProps {
  selected: boolean;
  onClick: () => void;
  title: string;
  description?: string;
  trailing?: ReactNode;
  compact?: boolean;
}

export function ChoiceCard({
  selected,
  onClick,
  title,
  description,
  trailing,
  compact,
}: ChoiceCardProps) {
  return (
    <button
      type="button"
      onClick={onClick}
      className={[
        "w-full text-left rounded-2xl border bg-white transition shadow-[0_1px_2px_rgba(15,23,42,0.04)]",
        compact ? "px-4 py-3" : "px-5 py-4",
        selected
          ? "border-slate-900 ring-2 ring-slate-900/5"
          : "border-slate-200 hover:border-slate-300",
      ].join(" ")}
    >
      <div className="flex items-start gap-3">
        <span
          className={[
            "mt-0.5 inline-flex h-5 w-5 shrink-0 items-center justify-center rounded-full border",
            selected
              ? "border-slate-900 bg-slate-900 text-white"
              : "border-slate-300 bg-white",
          ].join(" ")}
          aria-hidden="true"
        >
          {selected ? (
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
        <span className="flex-1">
          <span className="block text-sm font-medium text-slate-900">
            {title}
          </span>
          {description ? (
            <span className="mt-0.5 block text-xs text-slate-500">
              {description}
            </span>
          ) : null}
        </span>
        {trailing}
      </div>
    </button>
  );
}

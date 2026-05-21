import type { ReactNode } from "react";

export type StatusTone =
  | "complete"
  | "review"
  | "missing"
  | "info"
  | "neutral";

const TONE_CLASSES: Record<StatusTone, string> = {
  complete: "bg-emerald-50 text-emerald-700 ring-emerald-200",
  review: "bg-amber-50 text-amber-700 ring-amber-200",
  missing: "bg-red-50 text-red-700 ring-red-200",
  info: "bg-blue-50 text-blue-700 ring-blue-200",
  neutral: "bg-slate-100 text-slate-600 ring-slate-200",
};

interface StatusBadgeProps {
  tone?: StatusTone;
  children: ReactNode;
  className?: string;
}

export function StatusBadge({
  tone = "neutral",
  children,
  className = "",
}: StatusBadgeProps) {
  return (
    <span
      className={[
        "inline-flex items-center gap-1.5 rounded-full px-2.5 py-1 text-xs font-medium ring-1 ring-inset",
        TONE_CLASSES[tone],
        className,
      ].join(" ")}
    >
      <span
        className={[
          "h-1.5 w-1.5 rounded-full",
          tone === "complete"
            ? "bg-emerald-500"
            : tone === "review"
              ? "bg-amber-500"
              : tone === "missing"
                ? "bg-red-500"
                : tone === "info"
                  ? "bg-blue-500"
                  : "bg-slate-400",
        ].join(" ")}
      />
      {children}
    </span>
  );
}

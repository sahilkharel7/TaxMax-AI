import type { StepId } from "../types";

export interface StepDescriptor {
  id: StepId;
  label: string;
  shortLabel: string;
}

interface StepperProps {
  steps: StepDescriptor[];
  currentStep: StepId;
  onStepClick?: (id: StepId) => void;
}

export function Stepper({ steps, currentStep, onStepClick }: StepperProps) {
  const currentIndex = steps.findIndex((s) => s.id === currentStep);
  return (
    <nav aria-label="Progress" className="w-full">
      <ol className="flex w-full items-center gap-2">
        {steps.map((step, index) => {
          const isComplete = index < currentIndex;
          const isCurrent = index === currentIndex;
          const clickable = !!onStepClick && index <= currentIndex;
          return (
            <li key={step.id} className="flex flex-1 items-center gap-2">
              <button
                type="button"
                disabled={!clickable}
                onClick={() => clickable && onStepClick(step.id)}
                className={[
                  "group flex w-full items-center gap-2.5 rounded-full px-2.5 py-1.5 text-left transition",
                  clickable ? "hover:bg-slate-100" : "cursor-default",
                ].join(" ")}
              >
                <span
                  className={[
                    "flex h-6 w-6 shrink-0 items-center justify-center rounded-full text-[11px] font-semibold transition",
                    isComplete
                      ? "bg-slate-900 text-white"
                      : isCurrent
                        ? "bg-slate-900 text-white ring-4 ring-slate-900/10"
                        : "bg-slate-100 text-slate-500",
                  ].join(" ")}
                >
                  {isComplete ? (
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
                  ) : (
                    index + 1
                  )}
                </span>
                <span
                  className={[
                    "hidden truncate text-xs font-medium sm:inline",
                    isCurrent ? "text-slate-900" : "text-slate-500",
                  ].join(" ")}
                >
                  {step.shortLabel}
                </span>
              </button>
              {index < steps.length - 1 ? (
                <span
                  className={[
                    "h-px flex-1 transition",
                    isComplete ? "bg-slate-900/70" : "bg-slate-200",
                  ].join(" ")}
                />
              ) : null}
            </li>
          );
        })}
      </ol>
    </nav>
  );
}

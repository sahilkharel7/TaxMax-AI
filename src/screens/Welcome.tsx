import { Button } from "../components/ui/Button";

interface WelcomeProps {
  onStartUpload: () => void;
  onStartManual: () => void;
}

export function Welcome({ onStartUpload, onStartManual }: WelcomeProps) {
  return (
    <div className="animate-fade-up mx-auto flex max-w-3xl flex-col items-center px-4 py-10 sm:py-16 lg:py-24">
      <span className="mb-6 inline-flex items-center gap-2 rounded-full border border-slate-200 bg-white px-3 py-1 text-xs text-slate-600">
        <span className="h-1.5 w-1.5 rounded-full bg-emerald-500" />
        Prototype · United States · Tax Year 2024
      </span>

      <h1 className="text-center text-4xl font-semibold tracking-tight text-slate-900 sm:text-5xl lg:text-6xl">
        File smarter with TaxMax AI
      </h1>
      <p className="mt-5 max-w-xl text-center text-base text-slate-500 sm:text-lg">
        Upload your tax documents or enter your information manually. TaxMax AI
        helps organize, review, and explain your return — step by step.
      </p>

      <div className="mt-8 flex w-full max-w-md flex-col gap-3 sm:flex-row">
        <Button
          size="lg"
          variant="primary"
          fullWidth
          onClick={onStartUpload}
          leadingIcon={<UploadIcon />}
        >
          Start with document upload
        </Button>
        <Button
          size="lg"
          variant="secondary"
          fullWidth
          onClick={onStartManual}
          leadingIcon={<PencilIcon />}
        >
          Enter manually
        </Button>
      </div>

      <div className="mt-14 grid w-full max-w-3xl grid-cols-1 gap-3 sm:grid-cols-3">
        <Feature
          icon={<ShieldIcon />}
          title="Encrypted upload"
          body="Your documents are encrypted in transit and at rest."
        />
        <Feature
          icon={<EyeIcon />}
          title="Review before submission"
          body="You confirm every field before anything moves forward."
        />
        <Feature
          icon={<TrashIcon />}
          title="Delete anytime"
          body="Remove uploaded documents from your session whenever you want."
        />
      </div>

      <p className="mt-12 max-w-xl text-center text-xs text-slate-400">
        TaxMax AI provides AI-assisted preparation support. It does not provide
        legal or tax advice. E-filing is not available in this prototype.
      </p>
    </div>
  );
}

function Feature({
  icon,
  title,
  body,
}: {
  icon: React.ReactNode;
  title: string;
  body: string;
}) {
  return (
    <div className="flex items-start gap-3 rounded-2xl border border-slate-200/80 bg-white p-4">
      <span className="inline-flex h-9 w-9 items-center justify-center rounded-xl bg-slate-50 text-slate-700">
        {icon}
      </span>
      <div>
        <p className="text-sm font-medium text-slate-900">{title}</p>
        <p className="mt-0.5 text-xs text-slate-500">{body}</p>
      </div>
    </div>
  );
}

function UploadIcon() {
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
      <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4" />
      <polyline points="17 8 12 3 7 8" />
      <line x1="12" y1="3" x2="12" y2="15" />
    </svg>
  );
}
function PencilIcon() {
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
      <path d="M12 20h9" />
      <path d="M16.5 3.5a2.121 2.121 0 0 1 3 3L7 19l-4 1 1-4z" />
    </svg>
  );
}
function ShieldIcon() {
  return (
    <svg
      width="18"
      height="18"
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth="2"
      strokeLinecap="round"
      strokeLinejoin="round"
    >
      <path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z" />
    </svg>
  );
}
function EyeIcon() {
  return (
    <svg
      width="18"
      height="18"
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth="2"
      strokeLinecap="round"
      strokeLinejoin="round"
    >
      <path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8S1 12 1 12z" />
      <circle cx="12" cy="12" r="3" />
    </svg>
  );
}
function TrashIcon() {
  return (
    <svg
      width="18"
      height="18"
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth="2"
      strokeLinecap="round"
      strokeLinejoin="round"
    >
      <polyline points="3 6 5 6 21 6" />
      <path d="M19 6l-1 14a2 2 0 0 1-2 2H8a2 2 0 0 1-2-2L5 6" />
    </svg>
  );
}

import {
  useBackendHealth,
  type BackendHealthStatus,
} from "../hooks/useBackendHealth";

interface HeaderProps {
  onToggleChat: () => void;
  chatOpen: boolean;
}

export function Header({ onToggleChat, chatOpen }: HeaderProps) {
  const health = useBackendHealth();

  return (
    <header className="sticky top-0 z-40 border-b border-slate-200/70 bg-white/80 backdrop-blur">
      <div className="mx-auto flex h-14 max-w-7xl items-center justify-between px-4 sm:px-6">
        <a href="/" className="flex items-center gap-2">
          <Logo />
          <span className="text-[15px] font-semibold tracking-tight text-slate-900">
            TaxMax<span className="text-slate-400"> AI</span>
          </span>
        </a>

        <div className="hidden items-center gap-5 text-xs text-slate-500 sm:flex">
          <Trust label="Encrypted upload" />
          <Trust label="You control your documents" />
          <Trust label="Review before submission" />
        </div>

        <div className="flex items-center gap-2">
          <BackendStatus status={health.status} service={health.service} />
          <button
            type="button"
            onClick={onToggleChat}
            className="inline-flex h-9 items-center gap-2 rounded-full border border-slate-200 bg-white px-3 text-xs font-medium text-slate-700 hover:border-slate-300 lg:hidden"
          >
            <ChatIcon />
            {chatOpen ? "Hide guide" : "Open guide"}
          </button>
        </div>
      </div>
    </header>
  );
}

function Logo() {
  return (
    <span className="inline-flex h-7 w-7 items-center justify-center rounded-lg bg-slate-900 text-[13px] font-bold text-white">
      T
    </span>
  );
}

function Trust({ label }: { label: string }) {
  return (
    <span className="inline-flex items-center gap-1.5">
      <svg
        width="14"
        height="14"
        viewBox="0 0 24 24"
        fill="none"
        stroke="currentColor"
        strokeWidth="2"
        strokeLinecap="round"
        strokeLinejoin="round"
        className="text-emerald-500"
      >
        <path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z" />
      </svg>
      {label}
    </span>
  );
}

function BackendStatus({
  status,
  service,
}: {
  status: BackendHealthStatus;
  service?: string;
}) {
  const isMockMode = typeof service === "string" && /mock/i.test(service);
  const tone =
    status === "online"
      ? "text-emerald-600"
      : status === "offline"
        ? "text-rose-600"
        : "text-slate-400";

  const label =
    status === "online"
      ? isMockMode
        ? "Mock mode"
        : `API connected${service ? ` · ${service}` : ""}`
      : status === "offline"
        ? "API offline"
        : "Checking API…";

  return (
    <span
      className="hidden items-center gap-1.5 rounded-full border border-slate-200 bg-white px-2.5 py-1 text-[11px] font-medium md:inline-flex"
      title={label}
    >
      <span
        className={[
          "inline-block h-1.5 w-1.5 rounded-full",
          status === "online"
            ? "bg-emerald-500"
            : status === "offline"
              ? "bg-rose-500"
              : "animate-pulse bg-slate-400",
        ].join(" ")}
      />
      <span className={tone}>{label}</span>
    </span>
  );
}

function ChatIcon() {
  return (
    <svg
      width="14"
      height="14"
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth="2"
      strokeLinecap="round"
      strokeLinejoin="round"
    >
      <path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z" />
    </svg>
  );
}

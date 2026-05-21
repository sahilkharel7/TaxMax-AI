import { useEffect, useMemo, useRef, useState, type FormEvent } from "react";
import type { ChatMessage, StepId } from "../types";
import {
  mockChatReply,
  STEP_CONTEXT_HINTS,
  SUGGESTED_PROMPTS,
} from "../data/mockData";

interface ChatbotSidebarProps {
  step: StepId;
  open: boolean;
  onClose: () => void;
}

function welcomeContent(step: StepId): string {
  return (
    "Hi, I’m TaxMax Guide. I can explain tax terms and help you move through the app. " +
    (STEP_CONTEXT_HINTS[step] ??
      "Ask me anything about your documents or the steps ahead.")
  );
}

export function ChatbotSidebar({ step, open, onClose }: ChatbotSidebarProps) {
  // We store only the messages the user has produced (and their replies).
  // The welcome message is derived from the current step on each render so it
  // stays contextual without needing an effect.
  const [history, setHistory] = useState<ChatMessage[]>([]);
  const [input, setInput] = useState("");
  const [thinking, setThinking] = useState(false);
  const listRef = useRef<HTMLDivElement>(null);

  const welcome: ChatMessage = {
    id: "welcome",
    role: "assistant",
    content: welcomeContent(step),
  };
  const messages: ChatMessage[] = [welcome, ...history];

  useEffect(() => {
    const el = listRef.current;
    if (!el) return;
    el.scrollTo({ top: el.scrollHeight, behavior: "smooth" });
  }, [messages.length, thinking]);

  const placeholders = useMemo(() => SUGGESTED_PROMPTS.slice(0, 6), []);

  function sendMessage(text: string) {
    const trimmed = text.trim();
    if (!trimmed) return;
    const userMsg: ChatMessage = {
      id: crypto.randomUUID(),
      role: "user",
      content: trimmed,
    };
    setHistory((prev) => [...prev, userMsg]);
    setInput("");
    setThinking(true);
    window.setTimeout(() => {
      const reply: ChatMessage = {
        id: crypto.randomUUID(),
        role: "assistant",
        content: mockChatReply(trimmed),
      };
      setHistory((prev) => [...prev, reply]);
      setThinking(false);
    }, 650);
  }

  function onSubmit(e: FormEvent) {
    e.preventDefault();
    sendMessage(input);
  }

  return (
    <>
      {/* Mobile backdrop */}
      <div
        className={[
          "fixed inset-0 z-40 bg-slate-900/30 transition-opacity lg:hidden",
          open ? "opacity-100" : "pointer-events-none opacity-0",
        ].join(" ")}
        onClick={onClose}
        aria-hidden="true"
      />

      <aside
        className={[
          "fixed inset-y-0 right-0 z-50 flex w-[360px] max-w-[92vw] flex-col border-l border-slate-200 bg-white",
          "transition-transform duration-300 ease-out lg:static lg:translate-x-0 lg:shadow-none",
          open ? "translate-x-0 shadow-2xl" : "translate-x-full lg:translate-x-0",
        ].join(" ")}
        aria-label="TaxMax Guide chatbot"
      >
        <div className="flex items-center justify-between border-b border-slate-200/80 px-4 py-3">
          <div className="flex items-center gap-2">
            <span className="inline-flex h-7 w-7 items-center justify-center rounded-full bg-blue-50 text-blue-600">
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
                <path d="M12 2a4 4 0 0 1 4 4v1h1a4 4 0 0 1 4 4v6a4 4 0 0 1-4 4H7a4 4 0 0 1-4-4v-6a4 4 0 0 1 4-4h1V6a4 4 0 0 1 4-4z" />
                <circle cx="9" cy="14" r="1" />
                <circle cx="15" cy="14" r="1" />
              </svg>
            </span>
            <div>
              <p className="text-sm font-semibold text-slate-900">
                TaxMax Guide
              </p>
              <p className="text-[11px] text-slate-500">
                Contextual help · Step-aware
              </p>
            </div>
          </div>
          <button
            type="button"
            onClick={onClose}
            className="rounded-md p-1.5 text-slate-500 hover:bg-slate-100 lg:hidden"
            aria-label="Close guide"
          >
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
              <path d="M18 6L6 18" />
              <path d="M6 6l12 12" />
            </svg>
          </button>
        </div>

        <div
          ref={listRef}
          className="scrollbar-thin flex-1 space-y-3 overflow-y-auto px-4 py-4"
        >
          {messages.map((m) => (
            <div
              key={m.id}
              className={
                m.role === "user"
                  ? "ml-auto max-w-[85%] rounded-2xl rounded-br-sm bg-slate-900 px-3.5 py-2 text-sm text-white"
                  : "mr-auto max-w-[90%] whitespace-pre-wrap rounded-2xl rounded-bl-sm bg-slate-100 px-3.5 py-2 text-sm text-slate-800"
              }
            >
              {m.content}
            </div>
          ))}
          {thinking ? (
            <div className="mr-auto inline-flex gap-1 rounded-2xl rounded-bl-sm bg-slate-100 px-3.5 py-2.5">
              <Dot />
              <Dot delay={150} />
              <Dot delay={300} />
            </div>
          ) : null}
        </div>

        {messages.length <= 2 ? (
          <div className="border-t border-slate-200/80 px-4 py-3">
            <p className="mb-2 text-[11px] font-medium uppercase tracking-wide text-slate-400">
              Suggested
            </p>
            <div className="flex flex-wrap gap-1.5">
              {placeholders.map((p) => (
                <button
                  key={p}
                  type="button"
                  onClick={() => sendMessage(p)}
                  className="rounded-full border border-slate-200 bg-white px-2.5 py-1 text-[11px] text-slate-700 transition hover:border-slate-300 hover:bg-slate-50"
                >
                  {p}
                </button>
              ))}
            </div>
          </div>
        ) : null}

        <form
          onSubmit={onSubmit}
          className="border-t border-slate-200/80 px-3 pb-3 pt-3"
        >
          <div className="flex items-end gap-2 rounded-2xl border border-slate-200 bg-white px-2.5 py-1.5 focus-within:border-slate-900">
            <textarea
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyDown={(e) => {
                if (e.key === "Enter" && !e.shiftKey) {
                  e.preventDefault();
                  sendMessage(input);
                }
              }}
              rows={1}
              placeholder="Ask about W-2s, 1098-T, filing status…"
              className="max-h-32 min-h-[24px] flex-1 resize-none bg-transparent py-1 text-sm outline-none placeholder:text-slate-400"
            />
            <button
              type="submit"
              disabled={!input.trim() || thinking}
              className="inline-flex h-8 w-8 shrink-0 items-center justify-center rounded-lg bg-slate-900 text-white transition disabled:bg-slate-300"
              aria-label="Send"
            >
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
                <path d="M22 2L11 13" />
                <path d="M22 2l-7 20-4-9-9-4 20-7z" />
              </svg>
            </button>
          </div>
          <p className="mt-2 text-[10.5px] leading-snug text-slate-400">
            I can explain tax terms and guide you through the app, but I do not
            replace a qualified tax professional.
          </p>
        </form>
      </aside>
    </>
  );
}

function Dot({ delay = 0 }: { delay?: number }) {
  return (
    <span
      className="h-1.5 w-1.5 animate-bounce rounded-full bg-slate-400"
      style={{ animationDelay: `${delay}ms` }}
    />
  );
}

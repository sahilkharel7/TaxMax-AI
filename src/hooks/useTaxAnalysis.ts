import { useEffect, useRef, useState } from "react";
import { ApiError, postAnalyze } from "../lib/api";
import type { TaxScenarioRequestBody, TaxAnalysisResponseBody } from "../lib/apiTypes";

export type AnalysisState =
  | { status: "idle" }
  | { status: "loading" }
  | { status: "success"; data: TaxAnalysisResponseBody }
  | { status: "error"; error: string };

interface UseTaxAnalysisOptions {
  /** When false, skip the network call entirely and stay idle. */
  enabled?: boolean;
  /** Stable JSON-serializable key controlling when to refetch. */
  cacheKey: string;
  buildScenario: () => TaxScenarioRequestBody;
}

export function useTaxAnalysis({
  enabled = true,
  cacheKey,
  buildScenario,
}: UseTaxAnalysisOptions): AnalysisState {
  const [state, setState] = useState<AnalysisState>({ status: "idle" });
  const lastKeyRef = useRef<string | null>(null);

  useEffect(() => {
    if (!enabled) {
      lastKeyRef.current = null;
      return;
    }
    if (lastKeyRef.current === cacheKey) return;

    const controller = new AbortController();
    let cancelled = false;
    lastKeyRef.current = cacheKey;

    void Promise.resolve().then(() => {
      if (!cancelled) setState({ status: "loading" });
    });

    (async () => {
      try {
        const result = await postAnalyze(buildScenario(), controller.signal);
        if (!cancelled) setState({ status: "success", data: result });
      } catch (err) {
        if (cancelled) return;
        if (err instanceof DOMException && err.name === "AbortError") return;
        const message =
          err instanceof ApiError ? err.message : "Analysis request failed";
        setState({ status: "error", error: message });
      }
    })();

    return () => {
      cancelled = true;
      controller.abort();
    };
    // We intentionally only depend on the cacheKey; buildScenario is captured
    // each time the key changes so callers don't need to memoize it.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [cacheKey, enabled]);

  return enabled ? state : { status: "idle" };
}

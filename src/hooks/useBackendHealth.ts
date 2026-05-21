import { useEffect, useState } from "react";
import { ApiError, getHealth, isBackendEnabled } from "../lib/api";

export type BackendHealthStatus = "checking" | "online" | "offline";

export interface BackendHealthState {
  status: BackendHealthStatus;
  service?: string;
  error?: string;
}

const POLL_INTERVAL_MS = 30_000;

export function useBackendHealth(): BackendHealthState {
  const [state, setState] = useState<BackendHealthState>({ status: "checking" });

  useEffect(() => {
    if (!isBackendEnabled()) {
      setState({ status: "online", service: "Mock mode" });
      return;
    }

    let cancelled = false;
    const controller = new AbortController();

    async function check(): Promise<void> {
      try {
        const result = await getHealth(controller.signal);
        if (!cancelled) {
          setState({ status: "online", service: result.service });
        }
      } catch (err) {
        if (cancelled) return;
        const message =
          err instanceof ApiError ? err.message : "Backend unreachable";
        setState({ status: "offline", error: message });
      }
    }

    void check();
    const interval = window.setInterval(() => {
      void check();
    }, POLL_INTERVAL_MS);

    return () => {
      cancelled = true;
      controller.abort();
      window.clearInterval(interval);
    };
  }, []);

  return state;
}

import { useEffect, useState } from "react";
import { ApiError, getHealth, isBackendEnabled } from "../lib/api";

export type BackendHealthStatus = "checking" | "online" | "offline";

export interface BackendHealthState {
  status: BackendHealthStatus;
  service?: string;
  error?: string;
}

const ONLINE_POLL_INTERVAL_MS = 30_000;
const OFFLINE_POLL_INTERVAL_MS = 3_000;

export function useBackendHealth(): BackendHealthState {
  const [state, setState] = useState<BackendHealthState>(() =>
    isBackendEnabled()
      ? { status: "checking" }
      : { status: "online", service: "Mock mode" },
  );

  useEffect(() => {
    if (!isBackendEnabled()) {
      return;
    }

    let cancelled = false;
    let timeoutId: number | undefined;
    const controller = new AbortController();
    let currentStatus: BackendHealthStatus = "checking";

    async function check(): Promise<void> {
      try {
        const result = await getHealth(controller.signal);
        if (!cancelled) {
          currentStatus = "online";
          setState({ status: "online", service: result.service });
        }
      } catch (err) {
        if (cancelled) return;
        currentStatus = "offline";
        const message =
          err instanceof ApiError ? err.message : "Backend unreachable";
        setState({ status: "offline", error: message });
      } finally {
        if (!cancelled) {
          const delay =
            currentStatus === "online"
              ? ONLINE_POLL_INTERVAL_MS
              : OFFLINE_POLL_INTERVAL_MS;
          timeoutId = window.setTimeout(() => {
            void check();
          }, delay);
        }
      }
    }

    void check();

    return () => {
      cancelled = true;
      controller.abort();
      if (timeoutId !== undefined) {
        window.clearTimeout(timeoutId);
      }
    };
  }, []);

  return state;
}

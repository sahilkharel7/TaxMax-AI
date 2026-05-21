import { useEffect, useState } from "react";
import { ApiError, postOptimize } from "../lib/api";
import type {
  TaxOptimizationResponseBody,
  TaxScenarioRequestBody,
} from "../lib/apiTypes";

type OptimizationState =
  | { status: "idle" }
  | { status: "loading" }
  | { status: "success"; data: TaxOptimizationResponseBody }
  | { status: "error"; error: ApiError | Error };

interface UseTaxOptimizationOptions {
  cacheKey: string;
  buildScenario: () => TaxScenarioRequestBody;
}

export function useTaxOptimization({
  cacheKey,
  buildScenario,
}: UseTaxOptimizationOptions): OptimizationState {
  const [state, setState] = useState<OptimizationState>({ status: "idle" });

  useEffect(() => {
    const controller = new AbortController();

    void Promise.resolve().then(() => {
      if (!controller.signal.aborted) {
        setState({ status: "loading" });
      }
    });

    postOptimize(buildScenario(), controller.signal)
      .then((data) => {
        if (!controller.signal.aborted) {
          setState({ status: "success", data });
        }
      })
      .catch((err: unknown) => {
        if (controller.signal.aborted) return;
        setState({
          status: "error",
          error:
            err instanceof Error
              ? err
              : new Error("Tax optimization request failed"),
        });
      });

    return () => controller.abort();
    // buildScenario is intentionally omitted; callers should key changes via cacheKey.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [cacheKey]);

  return state;
}

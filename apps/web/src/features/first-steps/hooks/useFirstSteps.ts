import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { usePathname } from "next/navigation";
import { useEffect } from "react";
import { firstStepsApi } from "@/features/first-steps/api/firstStepsApi";
import {
  FIRST_STEPS_POLL_INTERVAL_MS,
  FIRST_STEPS_QUERY_KEY,
} from "@/features/first-steps/constants";
import { toast } from "@/lib/toast";
import type {
  FirstStepStatus,
  FirstStepsResponse,
} from "@/types/features/firstStepsTypes";

interface UseFirstSteps {
  steps: FirstStepStatus[];
  doneCount: number;
  totalCount: number;
  /** False until loaded, once dismissed, and once every step is done. */
  isVisible: boolean;
  isDismissing: boolean;
  dismiss: () => void;
}

/** Whether the checklist still has something to show the user. */
const isChecklistOpen = (data: FirstStepsResponse): boolean =>
  !data.dismissed && data.steps.some((step) => !step.done);

/**
 * The activation checklist, shared by the banner and the widget through one
 * react-query cache so both surfaces retire together.
 *
 * Every `done` is server-derived, so the cache only goes stale when the user
 * completes a step somewhere else in the app. Window-focus refetching is off
 * globally and the widget stays mounted across routes, so freshness comes from
 * three places instead: arriving at a new route, mounting a surface, and — only
 * while the checklist is still open — a slow poll.
 */
export function useFirstSteps(): UseFirstSteps {
  const qc = useQueryClient();
  const pathname = usePathname();

  const { data } = useQuery({
    queryKey: FIRST_STEPS_QUERY_KEY,
    queryFn: firstStepsApi.fetch,
    refetchOnMount: "always",
    refetchInterval: ({ state }) =>
      state.data && isChecklistOpen(state.data)
        ? FIRST_STEPS_POLL_INTERVAL_MS
        : false,
  });

  useEffect(() => {
    qc.invalidateQueries({ queryKey: FIRST_STEPS_QUERY_KEY });
  }, [pathname, qc]);

  const dismissMutation = useMutation({
    mutationFn: firstStepsApi.dismiss,
    // The cached checklist is the source of truth for what to show; dismissing
    // only flips that one flag, so nothing here depends on the response body.
    onSuccess: () =>
      qc.setQueryData<FirstStepsResponse>(
        FIRST_STEPS_QUERY_KEY,
        (previous) => previous && { ...previous, dismissed: true },
      ),
    onError: () => toast.error("Couldn't hide the checklist."),
  });

  const steps = data?.steps ?? [];

  return {
    steps,
    doneCount: steps.filter((step) => step.done).length,
    totalCount: steps.length,
    isVisible: data !== undefined && isChecklistOpen(data),
    isDismissing: dismissMutation.isPending,
    dismiss: () => dismissMutation.mutate(),
  };
}

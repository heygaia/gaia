import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { firstStepsApi } from "@/features/first-steps/api/firstStepsApi";
import { FIRST_STEPS_QUERY_KEY } from "@/features/first-steps/constants";
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

/**
 * The activation checklist, shared by the banner and the widget through one
 * react-query cache so both surfaces retire together.
 */
export function useFirstSteps(): UseFirstSteps {
  const qc = useQueryClient();

  const { data } = useQuery({
    queryKey: FIRST_STEPS_QUERY_KEY,
    queryFn: firstStepsApi.fetch,
  });

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
  const doneCount = steps.filter((step) => step.done).length;
  const isVisible =
    data !== undefined && !data.dismissed && doneCount < steps.length;

  return {
    steps,
    doneCount,
    totalCount: steps.length,
    isVisible,
    isDismissing: dismissMutation.isPending,
    dismiss: () => dismissMutation.mutate(),
  };
}

import { apiService } from "@/lib/api/service";
import type { FirstStepsResponse } from "@/types/features/firstStepsTypes";

export const firstStepsApi = {
  // Every `done` flag is derived server-side; there is no endpoint to set one.
  fetch: (): Promise<FirstStepsResponse> =>
    apiService.get<FirstStepsResponse>("/users/me/first-steps", {
      silent: true,
    }),

  dismiss: (): Promise<void> =>
    apiService.post<void>("/users/me/first-steps/dismiss", undefined, {
      silent: true,
    }),
};

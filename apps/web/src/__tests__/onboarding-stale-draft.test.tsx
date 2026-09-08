// @vitest-environment jsdom
/**
 * A finished wizard leaves a draft in localStorage. When the account is reset
 * server-side (the dev reset script, an admin unset) that draft is a lie about
 * progress, and rehydrating it walked straight to the final stage and
 * re-completed onboarding with last run's answers on the first paint.
 *
 * `GET /user/me` reports an unset onboarding as `preferences: {}`, never as a
 * missing field, so "the server has preferences" has to mean a recorded
 * profession, not the presence of the object.
 */
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { act, renderHook } from "@testing-library/react";
import type { ReactNode } from "react";
import { beforeEach, describe, expect, it, vi } from "vitest";

const completeOnboarding = vi.fn();
const saveOnboardingPreferences = vi.fn();

vi.mock("@/features/onboarding/api/onboardingApi", () => ({
  completeOnboarding: (...args: unknown[]) => completeOnboarding(...args),
  saveOnboardingPreferences: (...args: unknown[]) =>
    saveOnboardingPreferences(...args),
  resetOnboarding: vi.fn(),
  mintLinkCode: vi.fn(),
}));
vi.mock("@/features/pricing/hooks/useIsPaid", () => ({
  useIsPaid: () => ({
    isPaid: true,
    isUnknown: false,
    hasEverSubscribed: true,
  }),
}));
vi.mock("@/lib/analytics", () => ({
  ANALYTICS_EVENTS: new Proxy({}, { get: (_, key) => String(key) }),
  trackEvent: vi.fn(),
}));
vi.mock("@/lib/toast", () => ({
  toast: { error: vi.fn(), success: vi.fn() },
}));

import type { UserInfo } from "@/features/auth/api/authApi";
import { CURRENT_USER_QUERY_KEY } from "@/features/auth/hooks/useCurrentUser";
import { useOnboarding } from "@/features/onboarding/hooks/useOnboarding";
import { initialState } from "@/features/onboarding/state/initial";
import {
  loadPersisted,
  savePersisted,
} from "@/features/onboarding/state/persist";

const USER_ID = "user1";

const resetUser: UserInfo = {
  user_id: USER_ID,
  name: "Alice",
  email: "alice@example.com",
  picture: "",
  // Exactly what the API returns after the subdocument was unset.
  onboarding: { completed: false, preferences: {} },
};

function renderWizard(user: UserInfo) {
  const client = new QueryClient();
  client.setQueryData(CURRENT_USER_QUERY_KEY, user, { updatedAt: Date.now() });
  const wrapper = ({ children }: { children: ReactNode }) => (
    <QueryClientProvider client={client}>{children}</QueryClientProvider>
  );
  return renderHook(() => useOnboarding(), { wrapper });
}

describe("a stale browser draft after a server-side reset", () => {
  beforeEach(() => {
    localStorage.clear();
    vi.clearAllMocks();
    savePersisted(USER_ID, {
      ...initialState,
      responses: { profession: "founder" },
      selectedNeeds: ["inbox", "calendar"],
      preferencesPersisted: true,
      paidRevealAcked: true,
      platformsConfirmed: true,
    });
  });

  it("starts over at question one and never submits", async () => {
    const { result } = renderWizard(resetUser);
    await act(async () => {
      await Promise.resolve();
    });

    expect(result.current.stage).toBe("questions");
    expect(result.current.state.responses).toEqual({});
    expect(completeOnboarding).not.toHaveBeenCalled();
    expect(saveOnboardingPreferences).not.toHaveBeenCalled();
    expect(loadPersisted(USER_ID)).toBeNull();
  });

  it("still resumes a draft the server backs", async () => {
    const { result } = renderWizard({
      ...resetUser,
      onboarding: {
        completed: false,
        preferences: { profession: "founder" },
      },
    });
    await act(async () => {
      await Promise.resolve();
    });

    expect(result.current.state.responses).toEqual({ profession: "founder" });
    expect(result.current.state.preferencesPersisted).toBe(true);
  });
});

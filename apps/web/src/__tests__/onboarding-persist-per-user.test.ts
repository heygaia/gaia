// @vitest-environment jsdom
/**
 * Wizard progress is cached in localStorage so a reload resumes where the user
 * left off. That cache belongs to one account: a second person signing up on
 * the same browser must start at question one, not inherit the previous
 * account's answers and land on the payment stage (D16, found on the live
 * click-through).
 */
import { renderHook } from "@testing-library/react";
import { useReducer } from "react";
import { beforeEach, describe, expect, it } from "vitest";

import { useOnboardingPersistence } from "@/features/onboarding/effects/useOnboardingPersistence";
import { initialState } from "@/features/onboarding/state/initial";
import {
  clearPersisted,
  loadPersisted,
  savePersisted,
} from "@/features/onboarding/state/persist";
import { reducer } from "@/features/onboarding/state/reducer";

const ALICE = "user_alice";
const BOB = "user_bob";

describe("wizard persistence is scoped to the signed-in user", () => {
  beforeEach(() => localStorage.clear());

  it("does not hand one user's progress to another", () => {
    savePersisted(ALICE, {
      ...initialState,
      questionIndex: 2,
      responses: { profession: "founder" },
    });

    expect(loadPersisted(BOB)).toBeNull();
    expect(loadPersisted(ALICE)?.questionIndex).toBe(2);
  });

  it("clears only the restarting user's cache", () => {
    savePersisted(ALICE, { ...initialState, questionIndex: 1 });
    savePersisted(BOB, { ...initialState, questionIndex: 2 });

    clearPersisted(ALICE);

    expect(loadPersisted(ALICE)).toBeNull();
    expect(loadPersisted(BOB)?.questionIndex).toBe(2);
  });
});

describe("useOnboardingPersistence follows the signed-in user", () => {
  beforeEach(() => localStorage.clear());

  it("re-hydrates when the user id changes instead of carrying the old state over", () => {
    savePersisted(ALICE, { ...initialState, questionIndex: 2 });

    const { result, rerender } = renderHook(
      ({ userId }: { userId: string }) => {
        const [state, dispatch] = useReducer(reducer, initialState);
        useOnboardingPersistence(userId, true, state, dispatch);
        return state;
      },
      { initialProps: { userId: ALICE } },
    );
    expect(result.current.questionIndex).toBe(2);

    rerender({ userId: BOB });

    expect(result.current.questionIndex).toBe(0);
    expect(loadPersisted(BOB)).toBeNull();
    expect(loadPersisted(ALICE)?.questionIndex).toBe(2);
  });
});

describe("the server outranks the browser draft", () => {
  beforeEach(() => localStorage.clear());

  const hydrate = (serverHasPreferences: boolean) =>
    renderHook(() => {
      const [state, dispatch] = useReducer(reducer, initialState);
      useOnboardingPersistence(ALICE, serverHasPreferences, state, dispatch);
      return state;
    }).result.current;

  it("drops a draft that claims persisted preferences the account no longer has", () => {
    // The shape a finished run leaves behind; after a server-side reset it
    // would walk straight through every stage and complete onboarding again.
    savePersisted(ALICE, {
      ...initialState,
      responses: { profession: "founder" },
      selectedNeeds: ["inbox", "calendar"],
      preferencesPersisted: true,
      paidRevealAcked: true,
      platformsConfirmed: true,
    });

    const state = hydrate(false);

    expect(state.preferencesPersisted).toBe(false);
    expect(state.platformsConfirmed).toBe(false);
    expect(state.responses).toEqual({});
    expect(loadPersisted(ALICE)).toBeNull();
  });

  it("keeps the draft while the account still has the preferences it recorded", () => {
    savePersisted(ALICE, {
      ...initialState,
      responses: { profession: "founder" },
      preferencesPersisted: true,
    });

    expect(hydrate(true).preferencesPersisted).toBe(true);
  });

  it("keeps a draft that never got as far as persisting preferences", () => {
    savePersisted(ALICE, { ...initialState, questionIndex: 1 });

    expect(hydrate(false).questionIndex).toBe(1);
  });
});

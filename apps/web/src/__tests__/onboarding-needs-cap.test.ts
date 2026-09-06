/**
 * Q2 is "pick up to two". The cap lives in the reducer, not only in the chip
 * styling, so a stale chip or a double tap can never submit a third need.
 */

import { describe, expect, it } from "vitest";

import { NEEDS_MAX_SELECTION } from "@/features/onboarding/constants";
import { initialState } from "@/features/onboarding/state/initial";
import { reducer } from "@/features/onboarding/state/reducer";

describe("Q2 pick cap", () => {
  it("ignores a pick past the cap and still allows un-picking", () => {
    let state = initialState;
    for (const value of ["inbox", "calendar", "research"]) {
      state = reducer(state, { type: "toggleNeed", value });
    }
    expect(state.selectedNeeds).toEqual(["inbox", "calendar"]);
    expect(state.selectedNeeds.length).toBe(NEEDS_MAX_SELECTION);

    state = reducer(state, { type: "toggleNeed", value: "calendar" });
    state = reducer(state, { type: "toggleNeed", value: "research" });
    expect(state.selectedNeeds).toEqual(["inbox", "research"]);
  });
});

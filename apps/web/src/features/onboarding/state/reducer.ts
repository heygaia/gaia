/**
 * Pure reducer for the onboarding flow. Every state mutation goes through
 * here — no component or effect mutates state directly. Action variants are
 * documented in `types.ts`.
 */

import { NEEDS_MAX_SELECTION, questions } from "../constants";
import { canSubmitNeeds, pickCount } from "./derive";
import { initialState } from "./initial";
import type { Action, OnboardingState } from "./types";

export function reducer(
  state: OnboardingState,
  action: Action,
): OnboardingState {
  switch (action.type) {
    case "draftProfession":
      return { ...state, draftProfession: action.value };

    case "answer": {
      const isLast = state.questionIndex >= questions.length - 1;
      return {
        ...state,
        responses: { ...state.responses, [action.field]: action.value },
        questionIndex: isLast ? questions.length : state.questionIndex + 1,
        draftProfession: null,
      };
    }

    // The cap is enforced here, not only by dimming chips: a double tap or a
    // stale chip must never submit a third need the API would reject.
    case "toggleNeed": {
      if (state.selectedNeeds.includes(action.value)) {
        return {
          ...state,
          selectedNeeds: state.selectedNeeds.filter((n) => n !== action.value),
        };
      }
      if (pickCount(state) >= NEEDS_MAX_SELECTION) return state;
      return {
        ...state,
        selectedNeeds: [...state.selectedNeeds, action.value],
      };
    }

    case "setOtherNeed":
      return { ...state, otherNeed: action.value };

    // Min-selection is enforced here, not only in the composer: the gate is
    // what the backend contract requires, so it lives with the transition.
    case "submitNeeds":
      if (!canSubmitNeeds(state)) return state;
      return { ...state, questionIndex: questions.length };

    case "preferencesPersisted":
      return { ...state, preferencesPersisted: true };

    case "ackPaidReveal":
      return { ...state, paidRevealAcked: true };

    case "platformConnected":
      return {
        ...state,
        connectedPlatform: action.platform,
        platformsConfirmed: true,
      };

    case "skipPlatforms":
      return { ...state, platformsConfirmed: true };

    case "restartStart":
      return { ...initialState, isRestarting: true };

    case "restartDone":
      return { ...state, isRestarting: false };

    case "hydrate":
      return { ...state, ...action.partial };

    case "hydrated":
      return { ...state, hydratedFor: action.userId };

    case "reset":
      return initialState;
  }
}

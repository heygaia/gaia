// @vitest-environment jsdom
/**
 * The composer's message attachments (workflow + calendar event) used to live
 * in two standalone persisted stores. They are now a composerStore slice, and
 * a one-time persist migration has to carry a selection made before the move
 * across — then drop the old keys so they can never be read again.
 */
import { beforeEach, describe, expect, it } from "vitest";

import { useComposerStore } from "@/stores/composerStore";
import type {
  SelectedCalendarEventData,
  SelectedWorkflowData,
} from "@/stores/composerStore.types";

const WORKFLOW: SelectedWorkflowData = {
  id: "wf_1",
  title: "Daily digest",
  description: "Summarise the day",
  steps: [],
};

const EVENT: SelectedCalendarEventData = {
  id: "evt_1",
  summary: "Standup",
  description: "",
  start: { dateTime: "2026-09-07T09:00:00Z" },
  end: { dateTime: "2026-09-07T09:15:00Z" },
};

const store = () => useComposerStore.getState();

describe("composerStore selections", () => {
  beforeEach(() => {
    store().clearSelectedWorkflow();
    store().clearSelectedCalendarEvent();
  });

  it("selects a workflow with auto-send and clears both fields together", () => {
    store().selectWorkflow(WORKFLOW, { autoSend: true });
    expect(store().selectedWorkflow).toEqual(WORKFLOW);
    expect(store().workflowAutoSend).toBe(true);

    store().clearSelectedWorkflow();
    expect(store().selectedWorkflow).toBeNull();
    expect(store().workflowAutoSend).toBe(false);
  });

  it("defaults auto-send off when no options are passed", () => {
    store().selectWorkflow(WORKFLOW);
    expect(store().workflowAutoSend).toBe(false);
  });

  it("selects and clears a calendar event", () => {
    store().selectCalendarEvent(EVENT);
    expect(store().selectedCalendarEvent).toEqual(EVENT);

    store().clearSelectedCalendarEvent();
    expect(store().selectedCalendarEvent).toBeNull();
  });
});

describe("composer-storage selection migration", () => {
  beforeEach(() => {
    localStorage.clear();
  });

  it("copies the two legacy selection keys into composer-storage and removes them", async () => {
    localStorage.setItem(
      "workflow-selection-storage",
      JSON.stringify({ state: { selectedWorkflow: WORKFLOW, autoSend: true } }),
    );
    localStorage.setItem(
      "calendar-event-selection-storage",
      JSON.stringify({ state: { selectedCalendarEvent: EVENT } }),
    );
    localStorage.setItem(
      "composer-storage",
      JSON.stringify({ state: { inputText: "draft" }, version: 0 }),
    );

    await useComposerStore.persist.rehydrate();

    expect(store().inputText).toBe("draft");
    expect(store().selectedWorkflow).toEqual(WORKFLOW);
    expect(store().workflowAutoSend).toBe(true);
    expect(store().selectedCalendarEvent).toEqual(EVENT);
    expect(localStorage.getItem("workflow-selection-storage")).toBeNull();
    expect(localStorage.getItem("calendar-event-selection-storage")).toBeNull();
  });

  it("imports the legacy keys on a fresh install with no composer-storage at all", async () => {
    // A version-gated migrate never runs when nothing was persisted yet; the
    // import has to happen on every rehydrate until the legacy keys are gone.
    localStorage.setItem(
      "workflow-selection-storage",
      JSON.stringify({
        state: { selectedWorkflow: WORKFLOW, autoSend: false },
      }),
    );

    await useComposerStore.persist.rehydrate();

    expect(store().selectedWorkflow).toEqual(WORKFLOW);
    expect(store().workflowAutoSend).toBe(false);
    expect(localStorage.getItem("workflow-selection-storage")).toBeNull();
  });

  it("is a no-op once the legacy keys are gone", async () => {
    store().selectWorkflow(WORKFLOW, { autoSend: true });

    await useComposerStore.persist.rehydrate();

    expect(store().selectedWorkflow).toEqual(WORKFLOW);
    expect(store().workflowAutoSend).toBe(true);
  });
});

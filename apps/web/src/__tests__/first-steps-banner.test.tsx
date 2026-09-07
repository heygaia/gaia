// @vitest-environment jsdom
/**
 * The banner's one contract: every checkbox mirrors server state and is
 * read-only, and clicking a row runs that step's action instead of toggling.
 */

import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";

const fetchFirstSteps = vi.fn();
const dismissFirstSteps = vi.fn();
const push = vi.fn();
const appendToInput = vi.fn();
const trackEvent = vi.fn();

vi.mock("@/features/first-steps/api/firstStepsApi", () => ({
  firstStepsApi: {
    fetch: () => fetchFirstSteps(),
    dismiss: () => dismissFirstSteps(),
  },
}));

vi.mock("next/navigation", () => ({
  useRouter: () => ({ push }),
}));

vi.mock("@/stores/composerStore", () => ({
  useAppendToInput: () => appendToInput,
}));

vi.mock("@/lib/analytics", () => ({
  ANALYTICS_EVENTS: { FIRST_STEPS_STEP_CLICKED: "first_steps:step_clicked" },
  trackEvent: (...args: unknown[]) => trackEvent(...args),
}));

vi.mock("@/lib/toast", () => ({
  toast: { error: vi.fn(), success: vi.fn() },
}));

import { FirstStepsBanner } from "@/features/first-steps/components/FirstStepsBanner";
import { SAY_HI_PROMPT } from "@/features/first-steps/constants";
import type { FirstStepsResponse } from "@/types/features/firstStepsTypes";

const TWO_DONE: FirstStepsResponse = {
  dismissed: false,
  steps: [
    { key: "say_hi", done: true },
    { key: "connect_integration", done: true },
    { key: "link_platform", done: false },
    { key: "create_workflow", done: false },
    { key: "publish_workflow", done: false },
  ],
};

describe("FirstStepsBanner", () => {
  let queryClient: QueryClient;

  beforeEach(() => {
    vi.clearAllMocks();
    fetchFirstSteps.mockResolvedValue(TWO_DONE);
    queryClient = new QueryClient({
      defaultOptions: {
        queries: { retry: false },
        mutations: { retry: false },
      },
    });
  });

  const renderBanner = () =>
    render(
      <QueryClientProvider client={queryClient}>
        <FirstStepsBanner />
      </QueryClientProvider>,
    );

  const checkbox = (label: string): HTMLInputElement =>
    screen.getByRole("checkbox", { name: label });

  it("mirrors server state and shows progress", async () => {
    renderBanner();
    await waitFor(() => expect(screen.getByText("2/5")).toBeDefined());

    expect(checkbox("Say hi").checked).toBe(true);
    expect(checkbox("Connect an integration").checked).toBe(true);
    expect(checkbox("Link a messaging app").checked).toBe(false);
  });

  it("runs the action on click without toggling the checkbox", async () => {
    renderBanner();
    await waitFor(() => expect(screen.getByText("2/5")).toBeDefined());

    fireEvent.click(screen.getByText("Connect an integration"));

    expect(push).toHaveBeenCalledTimes(1);
    expect(push).toHaveBeenCalledWith("/integrations");
    expect(trackEvent).toHaveBeenCalledTimes(1);
    expect(trackEvent).toHaveBeenCalledWith("first_steps:step_clicked", {
      step: "connect_integration",
      done: true,
      surface: "banner",
    });
    // A done step stays done: the checkbox reflects the server, never the click.
    expect(checkbox("Connect an integration").checked).toBe(true);

    fireEvent.click(screen.getByText("Link a messaging app"));
    expect(push).toHaveBeenLastCalledWith("/settings/linked-accounts");
    expect(checkbox("Link a messaging app").checked).toBe(false);
  });

  it("pre-fills the composer for the say-hi step", async () => {
    renderBanner();
    await waitFor(() => expect(screen.getByText("2/5")).toBeDefined());

    fireEvent.click(screen.getByText("Say hi"));

    expect(appendToInput).toHaveBeenCalledWith(SAY_HI_PROMPT);
    expect(push).toHaveBeenCalledWith("/c");
  });

  it("dismisses through the server and disappears", async () => {
    dismissFirstSteps.mockResolvedValue({ ...TWO_DONE, dismissed: true });
    renderBanner();
    await waitFor(() => expect(screen.getByText("2/5")).toBeDefined());

    fireEvent.click(screen.getByLabelText("Dismiss first steps"));

    await waitFor(() => expect(dismissFirstSteps).toHaveBeenCalledTimes(1));
    await waitFor(() => expect(screen.queryByText("2/5")).toBeNull());
  });

  it("stays hidden once every step is done", async () => {
    fetchFirstSteps.mockResolvedValue({
      dismissed: false,
      steps: TWO_DONE.steps.map((step) => ({ ...step, done: true })),
    });
    renderBanner();

    await waitFor(() => expect(fetchFirstSteps).toHaveBeenCalled());
    expect(screen.queryByText("First steps")).toBeNull();
  });
});

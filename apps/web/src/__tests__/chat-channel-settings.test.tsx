// @vitest-environment jsdom
/**
 * The two things the section has to actually do: reorder where GAIA texts you
 * first, and turn the daily check-ins off.
 */

import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";

const fetchPriority = vi.fn();
const updatePriority = vi.fn();
const fetchActivationSequence = vi.fn();
const updateActivationSequence = vi.fn();

vi.mock("@/features/settings/api/chatChannelApi", () => ({
  chatChannelApi: {
    fetchPriority: () => fetchPriority(),
    updatePriority: (order: string[]) => updatePriority(order),
    fetchActivationSequence: () => fetchActivationSequence(),
    updateActivationSequence: (optedOut: boolean) =>
      updateActivationSequence(optedOut),
  },
}));

vi.mock("@/lib/toast", () => ({
  toast: { error: vi.fn(), success: vi.fn() },
}));

import type { NotificationPlatform } from "@/features/notification/constants";
import { ChatChannelSettings } from "@/features/settings/components/ChatChannelSettings";

const linked: NotificationPlatform[] = ["telegram", "whatsapp"];

describe("ChatChannelSettings", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    fetchPriority.mockResolvedValue({ priority: ["telegram", "whatsapp"] });
    fetchActivationSequence.mockResolvedValue({ opted_out: false });
    updatePriority.mockImplementation((priority: string[]) =>
      Promise.resolve({ priority }),
    );
    updateActivationSequence.mockResolvedValue({ opted_out: true });
  });

  it("promotes the second platform and saves the new order", async () => {
    render(<ChatChannelSettings linkedPlatforms={linked} />);
    await waitFor(() =>
      expect(screen.getByText("Texts you here first")).toBeDefined(),
    );

    fireEvent.click(screen.getByLabelText("Move WhatsApp up"));

    await waitFor(() =>
      expect(updatePriority).toHaveBeenCalledWith(["whatsapp", "telegram"]),
    );
    await waitFor(() =>
      expect(screen.getByLabelText("Move WhatsApp up")).toHaveProperty(
        "disabled",
        true,
      ),
    );
  });

  it("opts out of the daily check-ins when the switch is turned off", async () => {
    render(<ChatChannelSettings linkedPlatforms={linked} />);
    const toggle = await screen.findByRole("switch", {
      name: "Daily check-ins for your first week",
    });
    await waitFor(() => expect(toggle).toHaveProperty("checked", true));

    fireEvent.click(toggle);

    await waitFor(() =>
      expect(updateActivationSequence).toHaveBeenCalledWith(true),
    );
  });
});

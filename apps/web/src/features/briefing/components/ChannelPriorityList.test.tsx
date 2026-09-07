// @vitest-environment jsdom
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";

import { briefingApi } from "@/features/briefing/api/briefingApi";
import { ChannelPriorityList } from "@/features/briefing/components/ChannelPriorityList";

/**
 * Reordering used to be pointer-only: the drag handle's `onPointerDown` was the
 * single entry point, so a keyboard user could focus a row and still have no way
 * to change or save the order. Each connected row now carries move-up/move-down
 * buttons that go through the same persist path as a drop.
 */

vi.mock("@/lib/toast", () => ({
  toast: { error: vi.fn(), success: vi.fn() },
}));

vi.mock("@/features/briefing/api/briefingApi", () => ({
  briefingApi: {
    fetchChannelPriority: vi.fn(),
    updateChannelPriority: vi.fn(),
  },
}));

const ALL_LINKED = {
  telegram: true,
  whatsapp: true,
  imessage: true,
  slack: true,
  discord: true,
} as const;

function renderList() {
  const client = new QueryClient({
    defaultOptions: { queries: { retry: false } },
  });
  return render(
    <QueryClientProvider client={client}>
      <ChannelPriorityList linkedMap={ALL_LINKED} />
    </QueryClientProvider>,
  );
}

describe("ChannelPriorityList", () => {
  beforeEach(() => {
    vi.mocked(briefingApi.fetchChannelPriority).mockResolvedValue({
      chat_channel_priority: [
        "telegram",
        "whatsapp",
        "imessage",
        "slack",
        "discord",
      ],
    });
    vi.mocked(briefingApi.updateChannelPriority).mockReset();
    vi.mocked(briefingApi.updateChannelPriority).mockResolvedValue({
      chat_channel_priority: [],
    });
  });

  it("persists a new order from the keyboard move controls", async () => {
    renderList();
    const moveUp = await screen.findByRole("button", {
      name: "Move iMessage up",
    });

    fireEvent.click(moveUp);

    await waitFor(() =>
      expect(briefingApi.updateChannelPriority).toHaveBeenCalledWith([
        "telegram",
        "imessage",
        "whatsapp",
        "slack",
        "discord",
      ]),
    );
  });

  it("disables the move controls at the ends of the list", async () => {
    renderList();

    const topUp = await screen.findByRole("button", {
      name: "Move Telegram up",
    });
    const bottomDown = await screen.findByRole("button", {
      name: "Move Discord down",
    });
    const topDown = await screen.findByRole("button", {
      name: "Move Telegram down",
    });

    expect(topUp.getAttribute("disabled")).not.toBeNull();
    expect(bottomDown.getAttribute("disabled")).not.toBeNull();
    expect(topDown.getAttribute("disabled")).toBeNull();
  });
});

// @vitest-environment jsdom
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { act, render, waitFor } from "@testing-library/react";
import type React from "react";
import { beforeEach, describe, expect, it, vi } from "vitest";

import { briefingApi } from "@/features/briefing/api/briefingApi";
import { useChannelPriority } from "@/features/briefing/hooks/useChannelPriority";
import type { NotificationPlatform } from "@/features/notification/constants";

/**
 * Regression: two drops in quick succession each fired their own
 * `save.mutate`, so two PATCHes were in flight against the same row at once.
 * The server persists them in arrival order, which is not the order they were
 * issued in — the stale order could land last and win. (React Query masked
 * this locally: it only runs the observer's `onSuccess` for the newest
 * mutation, so the cache looked right while the stored row did not.) Saves are
 * now serialized and coalesced onto the latest order, so the request the
 * server sees last is always the newest one.
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

const flush = () =>
  act(async () => {
    await Promise.resolve();
  });

interface HookHandle {
  linkedOrder: NotificationPlatform[];
  reorderLinked: (next: NotificationPlatform[]) => void;
  persist: () => void;
  moveLinked: (platform: NotificationPlatform, delta: -1 | 1) => void;
}

function renderHarness() {
  const client = new QueryClient({
    defaultOptions: { queries: { retry: false } },
  });
  const handle: { current: HookHandle | null } = { current: null };

  const Probe: React.FC = () => {
    handle.current = useChannelPriority(ALL_LINKED);
    return null;
  };

  render(
    <QueryClientProvider client={client}>
      <Probe />
    </QueryClientProvider>,
  );

  return { handle, client };
}

describe("useChannelPriority", () => {
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
  });

  it("never has two saves in flight and sends the newest order last", async () => {
    const sent: NotificationPlatform[][] = [];
    const resolvers: Array<() => void> = [];
    let inFlight = 0;
    let maxInFlight = 0;
    vi.mocked(briefingApi.updateChannelPriority).mockImplementation(
      (order: NotificationPlatform[]) => {
        sent.push(order);
        inFlight += 1;
        maxInFlight = Math.max(maxInFlight, inFlight);
        return new Promise((resolve) => {
          resolvers.push(() => {
            inFlight -= 1;
            resolve({ chat_channel_priority: order });
          });
        });
      },
    );

    const { handle, client } = renderHarness();
    await waitFor(() => expect(handle.current?.linkedOrder.length).toBe(5));

    const first: NotificationPlatform[] = [
      "whatsapp",
      "telegram",
      "imessage",
      "slack",
      "discord",
    ];
    const second: NotificationPlatform[] = [
      "discord",
      "slack",
      "imessage",
      "telegram",
      "whatsapp",
    ];

    // Two drops back to back, the second replacing the first.
    act(() => {
      handle.current?.reorderLinked(first);
    });
    act(() => {
      handle.current?.persist();
    });
    act(() => {
      handle.current?.reorderLinked(second);
    });
    act(() => {
      handle.current?.persist();
    });
    await flush();

    // Settle every in-flight request newest-first — the hostile ordering that
    // let the stale response win.
    while (resolvers.length > 0) {
      const pending = resolvers.splice(0, resolvers.length).reverse();
      for (const resolve of pending) {
        resolve();
        await flush();
      }
    }

    expect(maxInFlight).toBe(1);
    expect(sent.at(-1)).toEqual(second);
    expect(client.getQueryData(["briefing-preferences"])).toEqual({
      chat_channel_priority: second,
    });
  });

  it("moveLinked swaps with the neighbour and persists once", async () => {
    vi.mocked(briefingApi.updateChannelPriority).mockResolvedValue({
      chat_channel_priority: [],
    });

    const { handle } = renderHarness();
    await waitFor(() => expect(handle.current?.linkedOrder.length).toBe(5));

    act(() => {
      handle.current?.moveLinked("imessage", -1);
    });
    await flush();

    expect(handle.current?.linkedOrder).toEqual([
      "telegram",
      "imessage",
      "whatsapp",
      "slack",
      "discord",
    ]);
    expect(briefingApi.updateChannelPriority).toHaveBeenCalledTimes(1);
  });

  it("moveLinked at the edges is a no-op", async () => {
    vi.mocked(briefingApi.updateChannelPriority).mockResolvedValue({
      chat_channel_priority: [],
    });

    const { handle } = renderHarness();
    await waitFor(() => expect(handle.current?.linkedOrder.length).toBe(5));

    act(() => {
      handle.current?.moveLinked("telegram", -1);
      handle.current?.moveLinked("discord", 1);
    });
    await flush();

    expect(handle.current?.linkedOrder).toEqual([
      "telegram",
      "whatsapp",
      "imessage",
      "slack",
      "discord",
    ]);
    expect(briefingApi.updateChannelPriority).not.toHaveBeenCalled();
  });
});

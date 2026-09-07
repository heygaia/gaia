"use client";

import { useQuery, useQueryClient } from "@tanstack/react-query";
import { useEffect, useMemo, useRef, useState } from "react";
import {
  type BriefingPreferences,
  briefingApi,
} from "@/features/briefing/api/briefingApi";
import {
  NOTIFICATION_PLATFORMS,
  type NotificationPlatform,
} from "@/features/notification/constants";
import { toast } from "@/lib/toast";

const BRIEFING_PREFERENCES_QUERY_KEY = ["briefing-preferences"];

/**
 * Coerce a server-provided order into a full, de-duplicated permutation of the
 * known platforms — the UI always renders every platform, so drift or a partial
 * list can't drop one.
 */
function normalizeOrder(raw?: NotificationPlatform[]): NotificationPlatform[] {
  const known = new Set<NotificationPlatform>(NOTIFICATION_PLATFORMS);
  const seen = new Set<NotificationPlatform>();
  const result: NotificationPlatform[] = [];
  for (const platform of raw ?? []) {
    if (known.has(platform) && !seen.has(platform)) {
      result.push(platform);
      seen.add(platform);
    }
  }
  for (const platform of NOTIFICATION_PLATFORMS) {
    if (!seen.has(platform)) result.push(platform);
  }
  return result;
}

interface UseChannelPriorityResult {
  isLoading: boolean;
  /** Linked platforms, in priority order — the draggable rows. */
  linkedOrder: NotificationPlatform[];
  /** Unlinked platforms, pinned below and non-draggable. */
  unlinkedOrder: NotificationPlatform[];
  /** Apply a reordered linked list (fired continuously during a drag). */
  reorderLinked: (next: NotificationPlatform[]) => void;
  /** Persist the current order (fired on drop); reverts + toasts on failure. */
  persist: () => void;
  /** Move one linked platform up (-1) or down (+1) and persist — the keyboard path. */
  moveLinked: (platform: NotificationPlatform, delta: -1 | 1) => void;
}

/**
 * Owns the briefing channel-priority order: fetches it, tracks the live
 * (optimistic) order during a drag, and persists on drop with revert-on-error.
 * `linkedMap` marks which platforms have a connected account.
 */
export function useChannelPriority(
  linkedMap: Record<NotificationPlatform, boolean>,
): UseChannelPriorityResult {
  const queryClient = useQueryClient();
  const { data, isLoading } = useQuery({
    queryKey: BRIEFING_PREFERENCES_QUERY_KEY,
    queryFn: briefingApi.fetchChannelPriority,
    staleTime: 5 * 60 * 1000,
  });

  const serverOrder = useMemo(
    () => normalizeOrder(data?.chat_channel_priority),
    [data],
  );

  const [order, setOrder] = useState<NotificationPlatform[]>(serverOrder);
  useEffect(() => {
    setOrder(serverOrder);
  }, [serverOrder]);

  const linkedOrder = order.filter((platform) => linkedMap[platform]);
  const unlinkedOrder = order.filter((platform) => !linkedMap[platform]);

  // Saves are serialized, never concurrent: a drag can land several drops in a
  // row, and two in-flight PUTs can settle out of order, leaving the server and
  // the cache on an order the user already moved away from. Each save waits for
  // the previous one and then sends whatever the LATEST pending order is, so
  // intermediate orders are coalesced away rather than queued one request each.
  const pendingOrder = useRef<NotificationPlatform[] | null>(null);
  const saveChain = useRef<Promise<void>>(Promise.resolve());

  const save = (
    next: NotificationPlatform[],
    revertTo: NotificationPlatform[],
  ) => {
    pendingOrder.current = next;
    saveChain.current = saveChain.current.then(async () => {
      const latest = pendingOrder.current;
      // A save earlier in the chain already sent this order (or a newer one).
      if (!latest) return;
      pendingOrder.current = null;
      try {
        await briefingApi.updateChannelPriority(latest);
        queryClient.setQueryData<BriefingPreferences>(
          BRIEFING_PREFERENCES_QUERY_KEY,
          { chat_channel_priority: latest },
        );
      } catch {
        setOrder(revertTo);
        toast.error("Couldn't save your briefing channel order.");
      }
    });
  };

  // Reordering only moves the linked rows among themselves; unlinked platforms
  // keep their relative order at the tail so the stored list stays a full
  // permutation.
  const commit = (nextLinked: NotificationPlatform[]) => {
    const next = [...nextLinked, ...unlinkedOrder];
    setOrder(next);
    save(next, serverOrder);
  };

  const reorderLinked = (next: NotificationPlatform[]) => {
    setOrder([...next, ...unlinkedOrder]);
  };

  const persist = () => {
    commit(linkedOrder);
  };

  const moveLinked = (platform: NotificationPlatform, delta: -1 | 1) => {
    const from = linkedOrder.indexOf(platform);
    const to = from + delta;
    if (from < 0 || to < 0 || to >= linkedOrder.length) return;
    const next = [...linkedOrder];
    next[from] = linkedOrder[to];
    next[to] = platform;
    commit(next);
  };

  return {
    isLoading,
    linkedOrder,
    unlinkedOrder,
    reorderLinked,
    persist,
    moveLinked,
  };
}

"use client";

import { useEffect, useState } from "react";
import type { NotificationPlatform } from "@/features/notification/constants";
import { chatChannelApi } from "@/features/settings/api/chatChannelApi";
import {
  linkedInPriorityOrder,
  moveChannel,
} from "@/features/settings/utils/chatChannelOrder";
import { toast } from "@/lib/toast";

interface UseChatChannelSettings {
  /** The linked platforms in priority order — the rows the section renders. */
  linkedOrder: NotificationPlatform[];
  /** Whether the daily activation messages are still on. */
  dailyCheckIns: boolean;
  /** True while a reorder is in flight, so the arrows can't race each other. */
  saving: boolean;
  move: (index: number, direction: "up" | "down") => Promise<void>;
  setDailyCheckIns: (enabled: boolean) => Promise<void>;
}

/**
 * Owns "where GAIA texts you": the stored priority order and the daily
 * activation opt-out, both persisted immediately and rolled back on failure.
 */
export function useChatChannelSettings(
  linkedPlatforms: NotificationPlatform[],
): UseChatChannelSettings {
  const [order, setOrder] = useState<NotificationPlatform[]>([]);
  const [dailyCheckIns, setDailyCheckIns] = useState(true);
  const [saving, setSaving] = useState(false);

  useEffect(() => {
    Promise.all([
      chatChannelApi.fetchPriority(),
      chatChannelApi.fetchActivationSequence(),
    ]).then(([priority, activation]) => {
      setOrder(priority.priority);
      setDailyCheckIns(!activation.opted_out);
    });
  }, []);

  const linkedOrder = linkedInPriorityOrder(order, linkedPlatforms);

  const move = async (index: number, direction: "up" | "down") => {
    const nextLinked = moveChannel(linkedOrder, index, direction);
    if (nextLinked === linkedOrder) return;
    // Unlinked platforms stay at the tail, so relinking one later restores the
    // position the user chose for it rather than dropping it to the default.
    const linked = new Set(linkedPlatforms);
    const unlinked = order.filter((platform) => !linked.has(platform));
    const previous = order;
    setOrder([...nextLinked, ...unlinked]);
    setSaving(true);
    try {
      const saved = await chatChannelApi.updatePriority([
        ...nextLinked,
        ...unlinked,
      ]);
      setOrder(saved.priority);
    } catch {
      setOrder(previous);
      toast.error("Couldn't save where GAIA texts you.");
    } finally {
      setSaving(false);
    }
  };

  const toggleDailyCheckIns = async (enabled: boolean) => {
    setDailyCheckIns(enabled);
    try {
      await chatChannelApi.updateActivationSequence(!enabled);
    } catch {
      setDailyCheckIns(!enabled);
      toast.error("Couldn't save your daily check-in preference.");
    }
  };

  return {
    linkedOrder,
    dailyCheckIns,
    saving,
    move,
    setDailyCheckIns: toggleDailyCheckIns,
  };
}

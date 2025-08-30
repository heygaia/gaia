"use client";

/**
 * HydrationManager Component
 *
 * This component ensures proper hydration of Zustand persist stores in Next.js SSR.
 *
 * Problem:
 * When using Zustand's persist middleware with Next.js, hydration can sometimes fail
 * to properly restore state from localStorage. This component ensures all persisted
 * stores are properly rehydrated after the client-side mount.
 *
 * Solution:
 * By manually triggering rehydration after client-side mount, we ensure:
 * 1. All persisted state is properly loaded from localStorage
 * 2. Components have access to the correct persisted state immediately
 * 3. Consistent behavior across different pages and refresh scenarios
 *
 * This component triggers rehydration for all Zustand stores with persist middleware.
 */

import { useEffect } from "react";

import { useCalendarStore } from "@/stores/calendarStore";
import { useComposerStore } from "@/stores/composerStore";
import { useUIStore } from "@/stores/uiStore";
import { useUserStore } from "@/stores/userStore";
import { useWorkflowSelectionStore } from "@/stores/workflowSelectionStore";

const HydrationManager = () => {
  useEffect(() => {
    // Trigger rehydration for all persisted stores after client-side mount
    useUIStore.persist.rehydrate();
    useComposerStore.persist.rehydrate();
    useUserStore.persist.rehydrate();
    useWorkflowSelectionStore.persist.rehydrate();
    useCalendarStore.persist.rehydrate();
  }, []);

  return null;
};

export default HydrationManager;

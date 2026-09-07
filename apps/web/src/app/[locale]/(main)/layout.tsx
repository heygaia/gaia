"use client";

import { useDrag } from "@use-gesture/react";
import nextDynamic from "next/dynamic";
import { type ReactNode, useEffect, useRef, useState } from "react";
import HeaderManager from "@/components/layout/headers/HeaderManager";
import StatusBanner from "@/components/layout/StatusBanner";
import Sidebar from "@/components/layout/sidebar/MainSidebar";
import RightSidebarSlot, {
  RightSidebarSlotProvider,
} from "@/components/layout/sidebar/RightSidebarSlot";
import { SidebarInset, SidebarProvider } from "@/components/ui/sidebar";
import { TooltipProvider } from "@/components/ui/tooltip";
import { useOnboardingGuard } from "@/features/auth/hooks/useOnboardingGuard";
import { useIsMobile } from "@/hooks/ui/useMobile";
import { useBackgroundSync } from "@/hooks/useBackgroundSync";
import ProvidersLayout from "@/layouts/ProvidersLayout";
import SidebarLayout, { CustomSidebarTrigger } from "@/layouts/SidebarLayout";
import { useChatStoreSync } from "@/stores/chatStore";
import { useLayoutSidebar } from "@/stores/layoutStore";

export const dynamic = "force-dynamic";

const UpgradeModal = nextDynamic(
  () =>
    import("@/features/pricing/components/UpgradeModal").then((m) => ({
      default: m.UpgradeModal,
    })),
  { ssr: false },
);
const CommandMenu = nextDynamic(
  () => import("@/features/search/components/CommandMenu"),
  { ssr: false },
);

const FirstStepsWidget = nextDynamic(
  () =>
    import("@/features/first-steps/components/FirstStepsWidget").then((m) => ({
      default: m.FirstStepsWidget,
    })),
  { ssr: false },
);

const WhatsNewModal = nextDynamic(
  () =>
    import("@/features/whats-new/components/WhatsNewModal").then((m) => ({
      default: m.WhatsNewModal,
    })),
  { ssr: false },
);

const HeaderSidebarTrigger = () => {
  return (
    <div className="">
      <CustomSidebarTrigger />
    </div>
  );
};

export default function MainLayout({ children }: { children: ReactNode }) {
  const { isOpen, isMobileOpen, setOpen, setMobileOpen } = useLayoutSidebar();
  const isMobile = useIsMobile();
  const [defaultOpen, setDefaultOpen] = useState(true);
  const dragRef = useRef<HTMLDivElement>(null);
  const [commandMenuOpen, setCommandMenuOpen] = useState(false);
  // Check if user needs onboarding
  useOnboardingGuard();
  useBackgroundSync();

  useChatStoreSync();

  // Auto-close sidebar on mobile when pathname changes
  useEffect(() => {
    if (isMobile && isMobileOpen) setMobileOpen(false);
  }, [isMobile, isMobileOpen, setMobileOpen]);

  useEffect(() => {
    if (isMobile) setDefaultOpen(false);
    else setDefaultOpen(true);
  }, [isMobile]);

  function handleOpenChange(open: boolean): void {
    if (isMobile) {
      setMobileOpen(open);
    } else {
      setOpen(open);
    }
  }

  // Get the current open state based on mobile/desktop
  const currentOpen = isMobile ? isMobileOpen : isOpen;

  // @warning: Removing the `target` option from useDrag will cause the HeroUI Buttons to not work properly.
  // For more details, see: https://github.com/hey-gaia/gaia/issues/44
  useDrag(
    ({ movement: [mx, my], last, tap }) => {
      // If this is just a tap, do nothing—allow click events to proceed.
      if (tap || !isMobile) return;

      if (last && Math.abs(mx) > Math.abs(my)) {
        if (mx > 0)
          // Swipe right to open
          setMobileOpen(true);
        else if (mx < 0)
          // Swipe left to close
          setMobileOpen(false);
      }
    },
    {
      filterTaps: true, // Taps are ignored for swipe detection.
      threshold: 10, // Minimal movement before detecting a swipe.
      axis: "x", // Only track horizontal swipes.
      target: dragRef,
      // preventDefault: false, // Prevent default touch actions to avoid conflicts.
      // eventOptions: { passive: false }, // Ensure we can prevent default behavior.
    },
  );

  return (
    <ProvidersLayout>
      <TooltipProvider>
        <RightSidebarSlotProvider>
          <SidebarProvider
            open={currentOpen}
            onOpenChange={handleOpenChange}
            defaultOpen={defaultOpen}
          >
            <div className="relative flex h-screen w-full dark" ref={dragRef}>
              <SidebarLayout>
                <Sidebar />
              </SidebarLayout>

              <SidebarInset className="flex h-screen min-w-0 w-auto flex-col bg-primary-bg">
                <StatusBanner />
                {/* Tapping anywhere outside the mobile sidebar dismisses it via
                  the Sheet's own modal overlay (see ui/sidebar), so the shell
                  needs no click handler of its own here. */}
                <header className="flex shrink-0 items-center justify-between p-2">
                  <HeaderSidebarTrigger />
                  <HeaderManager />
                </header>
                <main className="flex flex-1 flex-col overflow-hidden">
                  {/* <Suspense fallback={<SuspenseLoader />}> */}
                  {children}
                  {/* </Suspense> */}
                </main>
              </SidebarInset>

              <RightSidebarSlot />
            </div>

            {/* The one Pro upsell modal — non-dismissible when opened by
              enforcement (402 subscription_required), dismissible when the
              user opened it themselves. */}
            <UpgradeModal />

            {/* What's New Modal */}
            <WhatsNewModal />

            {/* Activation checklist; hides itself on /onboarding and /dashboard */}
            <FirstStepsWidget />

            {/* Global Command Menu */}
            <CommandMenu
              open={commandMenuOpen}
              onOpenChange={setCommandMenuOpen}
            />
          </SidebarProvider>
        </RightSidebarSlotProvider>
      </TooltipProvider>
    </ProvidersLayout>
  );
}

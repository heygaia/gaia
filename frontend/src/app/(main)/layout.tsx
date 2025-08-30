"use client";

import { useDrag } from "@use-gesture/react";
import { usePathname } from "next/navigation";
import { ReactNode, useEffect, useRef, useState } from "react";

import HeaderManager from "@/components/layout/headers/HeaderManager";
import Sidebar from "@/components/layout/sidebar/MainSidebar";
import { SidebarRight01Icon } from "@/components/shared/icons";
import { Button } from "@/components/ui/shadcn/button";
import {
  SidebarInset,
  SidebarProvider,
  useSidebar,
} from "@/components/ui/shadcn/sidebar";
import { TooltipProvider } from "@/components/ui/shadcn/tooltip";
import { useOnboardingGuard } from "@/features/auth/hooks/useOnboardingGuard";
import { useIsMobile } from "@/hooks/ui/useMobile";
import SidebarLayout from "@/layouts/SidebarLayout";
import { useSidebar as useUIStoreSidebar } from "@/stores/uiStore";

// Custom SidebarTrigger for header that matches the consistent styling
const HeaderSidebarTrigger = () => {
  const { toggleSidebar } = useSidebar();

  return (
    <Button
      aria-label="Toggle Sidebar"
      size="icon"
      variant="ghost"
      className="-ml-1 h-8 w-8 rounded-lg text-zinc-400 hover:bg-zinc-800/50 hover:text-zinc-100"
      onClick={toggleSidebar}
    >
      <SidebarRight01Icon className="max-h-5 min-h-5 max-w-5 min-w-5" />
    </Button>
  );
};

export default function MainLayout({ children }: { children: ReactNode }) {
  const pathname = usePathname();
  const { isOpen, isMobileOpen, setOpen, setMobileOpen } = useUIStoreSidebar();
  const isMobile = useIsMobile();
  const [defaultOpen, setDefaultOpen] = useState(true);
  const dragRef = useRef<HTMLDivElement>(null);

  // Check if user needs onboarding
  useOnboardingGuard();

  // Auto-close sidebar on mobile when pathname changes
  useEffect(() => {
    if (isMobile && isMobileOpen) setMobileOpen(false);
  }, [pathname, isMobile, isMobileOpen, setMobileOpen]);

  // Set default open state based on screen size
  useEffect(() => {
    if (isMobile) setDefaultOpen(false);
    else setDefaultOpen(true);
  }, [isMobile]);

  function closeOnTouch(): void {
    if (isMobile && (isMobileOpen || isOpen)) setMobileOpen(false);
  }

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
    <TooltipProvider>
      <SidebarProvider
        open={currentOpen}
        onOpenChange={handleOpenChange}
        defaultOpen={defaultOpen}
      >
        <div
          className="flex min-h-screen w-full dark"
          style={{ touchAction: "pan-y" }}
          ref={dragRef}
        >
          <SidebarLayout>
            <Sidebar />
          </SidebarLayout>

          <SidebarInset className="flex h-screen flex-col bg-[#1a1a1a]">
            <header
              className="flex flex-shrink-0 items-start justify-between px-4 pt-3"
              onClick={closeOnTouch}
            >
              {!currentOpen && <HeaderSidebarTrigger />}
              <HeaderManager />
            </header>
            <main className="flex flex-1 flex-col overflow-hidden">
              {children}
            </main>
          </SidebarInset>
        </div>
      </SidebarProvider>
    </TooltipProvider>
  );
}

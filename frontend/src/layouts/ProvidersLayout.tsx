"use client";

import { ReactNode, Suspense } from "react";

import SuspenseLoader from "@/components/shared/SuspenseLoader";
import { Toaster } from "@/components/ui/shadcn/sonner";
import LoginModal from "@/features/auth/components/LoginModal";
import { WorkflowSelectionProvider } from "@/features/chat/contexts/WorkflowSelectionContext";
import GlobalAuth from "@/hooks/providers/GlobalAuth";
import GlobalComposer from "@/hooks/providers/GlobalComposer";
import GlobalInterceptor from "@/hooks/providers/GlobalInterceptor";
import GlobalNotifications from "@/hooks/providers/GlobalNotifications";
import { HeroUIProvider } from "@/layouts/HeroUIProvider";
import QueryProvider from "@/layouts/QueryProvider";
import ReduxProviders from "@/redux/providers";

export default function ProvidersLayout({ children }: { children: ReactNode }) {
  return (
    <Suspense fallback={<SuspenseLoader fullHeight fullWidth />}>
      <HeroUIProvider>
        <QueryProvider>
          <ReduxProviders>
            <WorkflowSelectionProvider>
              <GlobalComposer>
                <GlobalInterceptor />
                <GlobalNotifications />
                <GlobalAuth />
                <LoginModal />

                <Toaster
                  closeButton
                  richColors
                  position="top-right"
                  theme="dark"
                />
                {children}
              </GlobalComposer>
            </WorkflowSelectionProvider>
          </ReduxProviders>
        </QueryProvider>
      </HeroUIProvider>
    </Suspense>
  );
}

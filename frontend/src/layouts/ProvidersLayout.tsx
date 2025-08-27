"use client";

import { ReactNode, Suspense } from "react";

import SuspenseLoader from "@/components/shared/SuspenseLoader";
import { Toaster } from "@/components/ui/shadcn/sonner";
import LoginModal from "@/features/auth/components/LoginModal";
import GlobalAuth from "@/hooks/providers/GlobalAuth";
import GlobalInterceptor from "@/hooks/providers/GlobalInterceptor";
import GlobalNotifications from "@/hooks/providers/GlobalNotifications";
import { HeroUIProvider } from "@/layouts/HeroUIProvider";
import QueryProvider from "@/layouts/QueryProvider";

export default function ProvidersLayout({ children }: { children: ReactNode }) {
  return (
    <Suspense fallback={<SuspenseLoader fullHeight fullWidth />}>
      <HeroUIProvider>
        <QueryProvider>
          <GlobalInterceptor />
          <GlobalNotifications />
          <GlobalAuth />
          <LoginModal />

          <Toaster closeButton richColors position="top-right" theme="dark" />
          {children}
        </QueryProvider>
      </HeroUIProvider>
    </Suspense>
  );
}

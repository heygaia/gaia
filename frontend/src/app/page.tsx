"use client";

import { ReactLenis } from "lenis/react";
import { lazy, Suspense, useEffect } from "react";

import HeroVideoDialog from "@/components/magicui/hero-video-dialog";
import SuspenseLoader from "@/components/shared/SuspenseLoader";
import HeroSection from "@/features/landing/components/hero/HeroSection";
import CommunitySection from "@/features/landing/components/sections/CommunitySection";

import LandingLayout from "./(landing)/layout";

const Personalised = lazy(
  () => import("@/features/landing/components/sections/Personalised"),
);
const Productivity = lazy(
  () => import("@/features/landing/components/sections/Productivity"),
);
const Tired = lazy(
  () =>
    import("@/features/landing/components/sections/TiredBoringAssistants"),
);
const ToolsShowcaseSection = lazy(
  () => import("@/features/landing/components/sections/ToolsShowcaseSection"),
);
const FAQAccordion = lazy(() =>
  import("@/features/pricing/components/FAQAccordion").then((module) => ({
    default: module.FAQAccordion,
  })),
);
const OpenSource = lazy(
  () => import("@/features/landing/components/sections/OpenSource"),
);
const FinalSection = lazy(
  () => import("@/features/landing/components/sections/FinalSection"),
);
const ChaoticWorkspaceSection = lazy(
  () =>
    import("@/features/landing/components/sections/ChaoticWorkspaceSection"),
);

export default function LandingPage() {
  useEffect(() => {
    document.documentElement.style.overflowY = "scroll";

    return () => {
      document.documentElement.style.overflowY = "auto";
    };
  }, []);

  return (
    <ReactLenis root>
      <LandingLayout>
        <div className="relative overflow-hidden">
          <HeroSection />
          <div className="relative z-10 mx-auto flex w-full items-center justify-center px-4 sm:px-6 lg:px-20">
            <HeroVideoDialog
              className="block w-full rounded-3xl"
              animationStyle="from-center"
              videoSrc="https://www.youtube.com/embed/K-ZbxMHxReM?si=U9Caazt9Ondagnr8"
              // thumbnailSrc="https://img.youtube.com/vi/K-ZbxMHxReM/maxresdefault.jpg"
              thumbnailSrc="/landing/hero.webp?q=80"
              thumbnailAlt="Hero Section Video"
            />
          </div>
          <div>
            <Suspense fallback={<SuspenseLoader />}>
              <ChaoticWorkspaceSection />
            </Suspense>
            <Suspense fallback={<SuspenseLoader />}>
              <ToolsShowcaseSection />
            </Suspense>
            <Suspense fallback={<SuspenseLoader />}>
              <Productivity />
            </Suspense>
            <Suspense fallback={<SuspenseLoader />}>
              <Tired />
            </Suspense>
            <Suspense fallback={<SuspenseLoader />}>
              <Personalised />
            </Suspense>
            <Suspense fallback={<SuspenseLoader />}>
              <FAQAccordion />
            </Suspense>
            <Suspense fallback={<SuspenseLoader />}>
              <OpenSource />
            </Suspense>
            <Suspense fallback={<SuspenseLoader />}>
              <CommunitySection />
            </Suspense>
            <Suspense fallback={<SuspenseLoader />}>
              <FinalSection />
            </Suspense>
          </div>
        </div>

        {/* Product Hunt Badge - Fixed Bottom Right */}
        {/* <div className="fixed right-6 bottom-6 z-50">
        <a
          href="https://www.producthunt.com/products/gaia-8010ee43-bc6e-40ef-989c-02c950a5b778?embed=true&utm_source=badge-featured&utm_medium=badge&utm_source=badge-gaia-6"
          target="_blank"
          rel="noopener noreferrer"
          className="block transition-transform"
        >
          <Image
            src="https://api.producthunt.com/widgets/embed-image/v1/featured.svg?post_id=1000528&theme=light&t=1754093183881"
            alt="GAIA - Proactive, Personal AI Assistant to boost your productivity | Product Hunt"
            width={250}
            height={54}
            className="drop-shadow-lg"
          />
        </a>
      </div> */}
      </LandingLayout>
    </ReactLenis>
  );
}

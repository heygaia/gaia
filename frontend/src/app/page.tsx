"use client";

import { lazy, useEffect } from "react";

import HeroSection from "@/features/landing/components/hero/HeroSection";
import { ReactLenis } from "lenis/react";

import HeroVideoDialog from "@/components/magicui/hero-video-dialog";
import Personalised from "@/features/landing/components/sections/new/Personalised";
import Productivity from "@/features/landing/components/sections/new/Productivity";
import Tired from "@/features/landing/components/sections/new/TiredBoringAssistants";
import WorkflowAutomation from "@/features/landing/components/sections/new/WorkflowAutomation";
import ToolsShowcaseSection from "@/features/landing/components/sections/ToolsShowcaseSection";
import { FAQAccordion } from "@/features/pricing/components/FAQAccordion";
import LandingLayout from "./(landing)/layout";
const FinalSection = lazy(
  () => import("@/features/landing/components/sections/FinalSection"),
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
          <div className="relative z-10 flex w-screen items-center justify-center p-10">
            <HeroVideoDialog
              className="block"
              animationStyle="from-center"
              videoSrc="https://www.youtube.com/embed/K-ZbxMHxReM?si=U9Caazt9Ondagnr8"
              thumbnailSrc="https://img.youtube.com/vi/K-ZbxMHxReM/maxresdefault.jpg"
              thumbnailAlt="Hero Section Video"
            />
          </div>
          <div>
            {/* <Description /> */}
            <ToolsShowcaseSection />
            <Productivity />
            <Tired />
            <Personalised />
            <WorkflowAutomation />
            <FAQAccordion />
            <FinalSection />
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

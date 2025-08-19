import React from "react";

import DummyComposer from "../demo/DummyComposer";
import LargeHeader from "../shared/LargeHeader";
import SectionLayout from "../shared/SectionLayout";

const FloatingIcon = ({
  src,
  alt,
  size = "w-12 h-12",
  className = "",
  side = "left",
}: {
  src: string;
  alt: string;
  size?: string;
  className?: string;
  side?: "left" | "right";
}) => (
  <div
    className={`absolute transition-all duration-300 hover:scale-110 ${className}`}
    style={{
      transform: side === "left" ? "rotate(-8deg)" : "rotate(8deg)",
    }}
  >
    <img src={src} alt={alt} className={`${size} object-contain`} />
  </div>
);

const ToolsShowcaseSection: React.FC = () => {
  return (
    <SectionLayout className="relative mt-20">
      <div
        className="absolute inset-0 z-[-1] w-full"
        style={{
          background:
            "radial-gradient(125% 150% at 50% 10%, #ffffff00 40%, #ffffff40 100%)",
        }}
      />
      <div className="relative h-screen w-full max-w-7xl overflow-hidden">
        <FloatingIcon
          src="/icons/notion.webp"
          alt="Notion"
          size="w-16 h-16"
          className="top-[8%] left-[5%]"
          side="left"
        />

        <FloatingIcon
          src="/icons/gmail.svg"
          alt="Gmail"
          size="w-14 h-14"
          className="top-[26%] left-[12%]"
          side="left"
        />

        {/* Floating Background Icons - Top Right Area */}
        <FloatingIcon
          src="/icons/googlecalendar.webp"
          alt="Google Calendar"
          size="w-15 h-15"
          className="top-[20%] right-[2%]"
          side="right"
        />

        <FloatingIcon
          src="/icons/slack.svg"
          alt="Slack"
          size="w-13 h-13"
          className="top-[7%] right-[13%]"
          side="right"
        />

        {/* Floating Background Icons - Mid Level */}
        <FloatingIcon
          src="/icons/google_docs.webp"
          alt="Google Docs"
          size="w-12 h-12"
          className="top-[45%] left-[3%]"
          side="left"
        />

        <FloatingIcon
          src="/icons/figma.svg"
          alt="Figma"
          size="w-12 h-12"
          className="top-[40%] right-[10%]"
          side="right"
        />

        {/* Floating Background Icons - Bottom Corners */}
        <FloatingIcon
          src="/icons/google_sheets.webp"
          alt="Google Sheets"
          size="w-10 h-10"
          className="bottom-[15%] left-[8%] opacity-70"
          side="left"
        />

        <FloatingIcon
          src="/icons/github3d.webp"
          alt="GitHub"
          size="w-11 h-11"
          className="bottom-[35%] left-[15%] opacity-80"
          side="left"
        />

        <FloatingIcon
          src="/icons/whatsapp.webp"
          alt="WhatsApp"
          size="w-10 h-10"
          className="right-[12%] bottom-[12%] opacity-70"
          side="right"
        />

        <FloatingIcon
          src="/icons/trello.svg"
          alt="Trello"
          size="w-11 h-11"
          className="right-[6%] bottom-[35%] opacity-80"
          side="right"
        />
        <div className="relative z-10 flex h-full flex-col items-center justify-center gap-4">
          <LargeHeader
            headingText="All Your Tools, One Assistant"
            subHeadingText="GAIA plugs into your digital world — so it can actually do things, not just talk."
            centered
          />

          <div className="mt-4 flex w-full items-center justify-center">
            <div className="w-full max-w-7xl min-w-full">
              <DummyComposer />
            </div>
          </div>
        </div>
      </div>
    </SectionLayout>
  );
};

export default ToolsShowcaseSection;

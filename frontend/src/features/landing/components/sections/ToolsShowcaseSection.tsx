import Image from "next/image";
import React from "react";

import DummyComposer from "../demo/DummyComposer";
import LargeHeader from "../shared/LargeHeader";
import SectionLayout from "../shared/SectionLayout";

const FloatingIcon = ({
  src,
  alt,
  size = 48,
  className = "",
  side = "left",
}: {
  src: string;
  alt: string;
  size?: number;
  className?: string;
  side?: "left" | "right";
}) => (
  <div
    className={`absolute transition-all duration-300 hover:scale-110 ${className}`}
    style={{
      transform: side === "left" ? "rotate(-8deg)" : "rotate(8deg)",
    }}
  >
    <Image
      src={src}
      alt={alt}
      width={size}
      height={size}
      className="object-contain"
      sizes={`${size}px`}
    />
  </div>
);

const ToolsShowcaseSection: React.FC = () => {
  return (
    <SectionLayout className="relative mt-20 px-4 sm:px-6 lg:px-8">
      <div
        className="absolute inset-0 z-[-1] w-full"
        style={{
          background:
            "radial-gradient(125% 150% at 50% 10%, #ffffff00 40%, #ffffff40 100%)",
        }}
      />
      <div className="relative h-screen w-full max-w-7xl overflow-hidden">
        <div className="relative z-10 flex h-full flex-col items-center justify-center gap-4 px-4 sm:px-0">
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

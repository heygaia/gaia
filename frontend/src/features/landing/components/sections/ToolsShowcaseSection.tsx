import React from "react";

import SectionLayout from "../shared/SectionLayout";
import LargeHeader from "../shared/LargeHeader";
import DummyComposer from "../demo/DummyComposer";
import Image from "next/image";
const ToolsShowcaseSection: React.FC = () => {
  return (
    <SectionLayout>
      <div className="h-screen w-full max-w-7xl">
        <div className="flex h-full flex-col items-center justify-center gap-4">
          <LargeHeader
            headingText="All Your Tools, One Assistant"
            subHeadingText="GAIA plugs into your digital world — so it can actually do things, not just talk."
          />

          {/* <Image
            src="https://cluely.com/_next/image?url=%2F_next%2Fstatic%2Fmedia%2Fmagnifier.37cce8ab.png&w=640&q=100"
            alt="test"
            width={300}
            className="absolute"
            height={300}
          />
            */}

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

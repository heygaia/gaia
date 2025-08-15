import { Mail as MailIcon } from "lucide-react";
import React from "react";

import LargeHeader from "../../shared/LargeHeader";
import SectionLayout from "../../shared/SectionLayout";
import MailAnimationWrapper from "./MailAnimationWrapper";

export default function Mail() {
  return (
    <SectionLayout>
      <LargeHeader
        chipText="Mail Automation"
        headingText="Your Inbox, Reimagined"
        subHeadingText="Compose, view, and manage your emails with simple commands. GAIA streamlines your entire workflow, turning natural language into instant action."
      />

      <div className="w-full max-w-6xl">
        <div className="relative">
          <div
            className="absolute -inset-px rounded-3xl border border-white/10 bg-gradient-to-br from-white/[0.02] to-transparent opacity-10 shadow-2xl shadow-black/40 blur-3xl backdrop-blur-2xl"
            aria-hidden="true"
          />
          <div className="relative overflow-hidden rounded-2xl border border-white/10 bg-gradient-to-br from-white/5 to-white/[0.02] p-4 shadow-2xl backdrop-blur-lg md:p-8">
            <MailAnimationWrapper />
          </div>
        </div>
      </div>
    </SectionLayout>
  );
}

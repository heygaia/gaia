// src/pages/features/Mail.tsx
import { Mail as MailIcon } from "lucide-react";
import React from "react";

import SectionChip from "../../shared/SectionChip";
import MailAnimationWrapper from "./MailAnimationWrapper";

export default function Mail() {
  return (
    <div className="relative min-h-screen overflow-hidden bg-[radial-gradient(ellipse_at_top_left,_#0f0f0f,_#09090b)] bg-cover bg-fixed bg-no-repeat">
      <div className="absolute inset-0 bg-[radial-gradient(circle_at_50%_50%,rgba(1,187,255,0.05),transparent_50%)]" />
      <div className="absolute inset-0 bg-[linear-gradient(to_right,#80808008_1px,transparent_1px),linear-gradient(to_bottom,#80808008_1px,transparent_1px)] bg-[size:32px_32px]" />

      <div className="relative z-10 mx-auto max-w-7xl px-4 py-20 sm:px-6 lg:px-8 lg:py-28">
        {/* Header Section */}
        <div className="mx-auto mb-12 max-w-3xl text-center md:mb-16">
          <SectionChip icon={MailIcon} text="Mail Automation" />
          <h1 className="mt-4 bg-gradient-to-r from-white via-white/80 to-gray-400 bg-clip-text pb-1 text-4xl font-bold tracking-tight text-transparent sm:text-5xl lg:text-6xl">
            Your Inbox, Reimagined
          </h1>
          <p className="mt-6 text-lg leading-8 text-gray-400 md:text-xl">
            Compose, view, and manage your emails with simple commands. GAIA
            streamlines your entire workflow, turning natural language into
            instant action.
          </p>
        </div>

        {/* Animation Section */}
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
    </div>
  );
}

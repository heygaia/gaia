import Image from "next/image";
import React, { useEffect, useRef, useState } from "react";

import SectionChip from "../shared/SectionChip";

const LargeHeader = ({
  chipText,
  headingText,
  subHeadingText,
}: {
  chipText: string;
  headingText: string;
  subHeadingText: string;
}) => (
  <div className="mb-16 text-center">
    <SectionChip text={chipText} />

    <h2 className="mb-6 bg-gradient-to-r from-white via-white to-gray-400 bg-clip-text text-4xl leading-tight font-medium text-transparent md:text-5xl lg:text-6xl">
      {headingText}
    </h2>

    <p className="mx-auto max-w-2xl text-xl leading-relaxed text-gray-400 md:text-2xl">
      {subHeadingText}
    </p>
  </div>
);

interface IntegrationCardProps {
  image?: string;
  alt?: string;
  className?: string;
  isBlurred?: boolean;
  isLarge?: boolean;
  delay?: number;
}

const IntegrationCard = ({
  image,
  alt = "Integration",
  className = "",
  isBlurred = false,
  isLarge = false,
  delay = 0,
}: IntegrationCardProps) => {
  const [isVisible, setIsVisible] = useState(false);
  const cardRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const timer = setTimeout(() => {
      setIsVisible(true);
    }, delay);

    return () => clearTimeout(timer);
  }, [delay]);

  return (
    <div
      ref={cardRef}
      className={`group relative flex aspect-square items-center justify-center rounded-2xl border border-white/10 bg-gradient-to-br from-white/5 to-white/[0.02] shadow-lg backdrop-blur-sm transition-all duration-500 ease-out hover:border-[#01BBFF]/20 hover:shadow-xl hover:shadow-[#01BBFF]/5 ${isLarge ? "w-28" : "w-24"} ${isBlurred ? "scale-90 opacity-40" : "scale-100 opacity-100"} ${isVisible ? "translate-y-0" : "translate-y-4"} ${className} `}
    >
      {image ? (
        <Image
          src={image}
          alt={alt}
          className={`${isLarge ? "h-16 w-16" : "h-12 w-12"} object-contain transition-all duration-300 group-hover:scale-110`}
          width={isLarge ? 64 : 48}
          height={isLarge ? 64 : 48}
        />
      ) : (
        <div className="h-8 w-8 animate-pulse rounded-lg bg-white/10" />
      )}

      {/* Subtle glow effect */}
      <div className="absolute inset-0 rounded-2xl bg-gradient-to-r from-[#01BBFF]/0 via-[#01BBFF]/5 to-[#01BBFF]/0 opacity-0 transition-opacity duration-300 group-hover:opacity-100" />
    </div>
  );
};

const integrations = [
  // First row - 4 items
  [
    {
      image:
        "https://upload.wikimedia.org/wikipedia/commons/thumb/6/66/Google_Docs_2020_Logo.svg/640px-Google_Docs_2020_Logo.svg.png",
      alt: "Google Docs",
      isBlurred: true,
    },
    {
      image:
        "https://upload.wikimedia.org/wikipedia/commons/thumb/a/ae/Google_Sheets_2020_Logo.svg/640px-Google_Sheets_2020_Logo.svg.png",
      alt: "Google Sheets",
    },
    {
      image:
        "https://upload.wikimedia.org/wikipedia/commons/thumb/1/16/Google_Slides_2020_Logo.svg/640px-Google_Slides_2020_Logo.svg.png",
      alt: "Google Slides",
    },
    {
      image:
        "https://cdn.jsdelivr.net/gh/devicons/devicon/icons/figma/figma-original.svg",
      alt: "Figma",
      isBlurred: true,
    },
  ],
  // Second row - 5 items (Main productivity tools with Notion center)
  [
    {
      image:
        "https://cdn.jsdelivr.net/gh/devicons/devicon/icons/trello/trello-plain.svg",
      alt: "Trello",
      isBlurred: true,
    },
    {
      image:
        "https://upload.wikimedia.org/wikipedia/commons/thumb/a/a5/Google_Calendar_icon_%282020%29.svg/640px-Google_Calendar_icon_%282020%29.svg.png",
      alt: "Google Calendar",
    },
    {
      image:
        "https://upload.wikimedia.org/wikipedia/commons/4/45/Notion_app_logo.png",
      alt: "Notion",
      isLarge: true,
    },
    {
      image:
        "https://upload.wikimedia.org/wikipedia/commons/7/7e/Gmail_icon_%282020%29.svg",
      alt: "Gmail",
    },
    {
      image:
        "https://cdn.jsdelivr.net/gh/devicons/devicon@latest/icons/linkedin/linkedin-original.svg",
      alt: "LinkedIn",
      isBlurred: true,
    },
  ],
  // Third row - 4 items
  [
    {
      image:
        "https://cdn.brandfetch.io/idZAyF9rlg/theme/light/symbol.svg?c=1dxbfHSJFAPEGdCLU4o5B",
      alt: "GitHub",
      isBlurred: true,
    },
    {
      image:
        "https://upload.wikimedia.org/wikipedia/commons/thumb/6/6b/WhatsApp.svg/1024px-WhatsApp.svg.png?20220228223904",
      alt: "WhatsApp",
    },
    {
      image:
        "https://cdn.jsdelivr.net/gh/devicons/devicon/icons/slack/slack-original.svg",
      alt: "Slack",
    },
    {
      image:
        "https://cdn.creazilla.com/icons/3254448/todoist-icon-icon-original.svg",
      alt: "Todoist",
      isBlurred: true,
    },
  ],
];

export default function IntegrationsSection() {
  const [isInView, setIsInView] = useState(false);
  const sectionRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const observer = new IntersectionObserver(
      ([entry]) => {
        if (entry.isIntersecting) {
          setIsInView(true);
        }
      },
      { threshold: 0.3 },
    );

    if (sectionRef.current) {
      observer.observe(sectionRef.current);
    }

    return () => observer.disconnect();
  }, []);

  return (
    <section
      ref={sectionRef}
      className="relative min-h-screen overflow-hidden bg-[radial-gradient(ellipse_at_top_left,_#0f0f0f,_#09090b)] bg-cover bg-fixed bg-no-repeat"
    >
      {/* Background effects */}
      <div className="absolute inset-0 bg-[radial-gradient(circle_at_50%_50%,rgba(1,187,255,0.03),transparent_50%)]" />
      <div className="absolute inset-0 bg-[linear-gradient(to_right,#80808008_1px,transparent_1px),linear-gradient(to_bottom,#80808008_1px,transparent_1px)] bg-[size:32px_32px]" />

      <div className="relative z-10 container mx-auto max-w-7xl px-4 py-20">
        <LargeHeader
          chipText="Coming Soon"
          headingText="All Your Tools, One Assistant"
          subHeadingText="GAIA plugs into your digital world — so it can actually do things, not just talk."
        />

        {/* Integration Grid */}
        <div className="mt-16 flex flex-col items-center gap-6">
          {integrations.map((row, rowIndex) => (
            <div
              key={rowIndex}
              className="flex items-center justify-center gap-4"
            >
              {row.map((integration, cardIndex) => (
                <IntegrationCard
                  key={cardIndex}
                  image={integration.image}
                  alt={integration.alt}
                  isBlurred={integration.isBlurred}
                  isLarge={integration.isLarge}
                  delay={isInView ? rowIndex * 100 + cardIndex * 50 : 0}
                />
              ))}
            </div>
          ))}
        </div>

        {/* Subtle connection lines */}
        <div className="pointer-events-none absolute inset-0">
          <div className="absolute top-1/2 left-1/2 h-96 w-96 -translate-x-1/2 -translate-y-1/2 opacity-10">
            {/* <div className="absolute inset-0 bg-gradient-to-r from-transparent via-[#01BBFF]/20 to-transparent transform rotate-45"></div> */}
            {/* <div className="absolute inset-0 bg-gradient-to-r from-transparent via-[#01BBFF]/20 to-transparent transform -rotate-45"></div> */}
          </div>
        </div>
      </div>
    </section>
  );
}

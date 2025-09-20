import Image from "next/image";
import React, { useEffect, useRef, useState } from "react";

import SectionChip from "../shared/SectionChip";

const LargeHeader = ({
  chipText,
  headingText,
  subHeadingText,
}: {
  chipText?: string;
  headingText: string;
  subHeadingText: string;
}) => (
  <div className="mb-16 text-center">
    {chipText && <SectionChip text={chipText} />}

    <h2 className="mb-6 bg-gradient-to-r from-white via-white to-gray-400 bg-clip-text text-4xl leading-tight font-medium text-transparent md:text-5xl lg:text-6xl">
      {headingText}
    </h2>

    <p className="mx-auto max-w-2xl text-xl leading-relaxed text-gray-300 md:text-2xl">
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
      className={`group relative flex aspect-square items-center justify-center rounded-3xl border border-white/10 bg-zinc-900 shadow-lg backdrop-blur-sm transition-all duration-500 ease-out hover:border-[#01BBFF]/20 hover:shadow-xl hover:shadow-[#01BBFF]/5 ${isLarge ? "w-28" : "w-24"} ${isBlurred ? "scale-90 opacity-40" : "scale-100 opacity-100"} ${isVisible ? "translate-y-0" : "translate-y-4"} ${className} `}
    >
      {image ? (
        <Image
          src={image}
          alt={alt}
          width={isLarge ? 64 : 48}
          height={isLarge ? 64 : 48}
          className={`object-contain transition-all duration-300 group-hover:scale-110`}
          sizes={isLarge ? "64px" : "48px"}
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
      image: "/images/icons/google_docs.webp",
      alt: "Google Docs",
      isBlurred: true,
    },
    {
      image: "/images/icons/google_sheets.webp",
      alt: "Google Sheets",
    },
    {
      image: "/images/icons/google_sides.webp",
      alt: "Google Slides",
    },
    {
      image: "/images/icons/figma.svg",
      alt: "Figma",
      isBlurred: true,
    },
  ],
  // Second row - 5 items (Main productivity tools with Notion center)
  [
    {
      image: "/images/icons/trello.svg",
      alt: "Trello",
      isBlurred: true,
    },
    {
      image: "/images/icons/googlecalendar.webp",
      alt: "Google Calendar",
    },
    {
      image: "/images/icons/notion.webp",
      alt: "Notion",
      isLarge: true,
    },
    {
      image: "/images/icons/gmail.svg",
      alt: "Gmail",
    },
    {
      image: "/images/icons/linkedin.svg",
      alt: "LinkedIn",
      isBlurred: true,
    },
  ],
  // Third row - 4 items
  [
    {
      image: "/images/icons/github3d.webp",
      alt: "GitHub",
      isBlurred: true,
    },
    {
      image: "/images/icons/whatsapp.webp",
      alt: "WhatsApp",
    },
    {
      image: "/images/icons/slack.svg",
      alt: "Slack",
    },
    {
      image: "/images/icons/todoist.svg",
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
    <section ref={sectionRef} className="relative min-h-screen overflow-hidden">
      <div className="relative z-10 container mx-auto max-w-7xl px-4 py-20">
        <LargeHeader
          headingText="All Your Tools, One Assistant"
          subHeadingText="GAIA plugs into your digital world — so it can actually do things, not just talk."
        />

        {/* Integration Grid */}
        <div className="mt-16 flex flex-col items-center gap-6">
          {integrations.map((row, rowIndex) => (
            <div
              key={rowIndex}
              className="flex items-center justify-center gap-3"
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

import Image from "next/image";
import { useCallback, useEffect, useState } from "react";

import {
  CheckmarkCircle02Icon,
  GlobalSearchIcon,
  InternetIcon,
} from "@/components/shared/icons";

import { cn } from "../../../../lib/utils";
import { SectionHeading } from "../../layouts/SectionHeader";

const webSearchImages = [
  { src: "/landing/web/0.webp", alt: "Web search Screenshot weather" },
  { src: "/landing/web/1.webp", alt: "Web search Screenshot 1" },
  { src: "/landing/web/2.webp", alt: "Web search Screenshot 2" },
  { src: "/landing/web/3.webp", alt: "Web search Screenshot 3" },
  { src: "/landing/web/4.webp", alt: "Web search Screenshot 4" },
];

const fetchWebpageImages = [
  { src: "/landing/web/fetch/0.webp", alt: "Fetch Webpage Screenshot 4" },
  { src: "/landing/web/fetch/1.webp", alt: "Fetch Webpage Screenshot 1" },
  { src: "/landing/web/fetch/3.webp", alt: "Fetch Webpage Screenshot 3" },
  { src: "/landing/web/fetch/2.webp", alt: "Fetch Webpage Screenshot 2" },
];

const ImageCarousel = ({
  images,
}: {
  images: { src: string; alt: string }[];
}) => {
  const [currentIndex, setCurrentIndex] = useState(0);

  const nextIndex = useCallback(() => {
    setCurrentIndex((prevIndex) => (prevIndex + 1) % images.length);
  }, [images.length]);

  useEffect(() => {
    const timer = setInterval(nextIndex, 20_000);
    return () => clearInterval(timer);
  }, [nextIndex]);

  const handleDotClick = useCallback((index: number) => {
    setCurrentIndex(index);
  }, []);

  return (
    <div className="relative h-[50vh] w-full">
      <div
        className="relative h-full w-full overflow-hidden rounded-lg"
        onClick={nextIndex}
      >
        {images.map((image, index) => (
          <div
            key={index}
            className={cn(
              "absolute h-full w-full cursor-pointer shadow-lg shadow-[#00bbff] transition-opacity duration-500 ease-in-out",
              index === currentIndex ? "opacity-100" : "opacity-0",
            )}
          >
            <Image
              src={image.src}
              alt={image.alt}
              fill
              className="rounded-2xl object-cover"
            />
          </div>
        ))}
      </div>

      <div className="relative top-2 flex justify-center space-x-2">
        {images.map((_, index) => (
          <button
            key={index}
            onClick={() => handleDotClick(index)}
            className={cn(
              "max-h-[10px] min-h-[10px] max-w-[10px] min-w-[10px] rounded-full transition",
              index === currentIndex
                ? "bg-primary"
                : "bg-gray-600 hover:bg-gray-400",
            )}
            aria-label={`Go to slide ${index + 1}`}
          />
        ))}
      </div>
    </div>
  );
};

export default function Internet() {
  return (
    <div className="flex w-screen items-center justify-center">
      <div className="flex w-screen max-w-(--breakpoint-xl) flex-col space-y-5">
        <div className="relative flex w-screen max-w-(--breakpoint-xl) flex-col items-start justify-start gap-11 p-3 sm:flex-row">
          <div className="flex h-full w-full flex-col items-center justify-between gap-5 rounded-3xl bg-zinc-900 p-0 pb-10 sm:gap-0 sm:p-7 sm:pb-7">
            <div className="min-h-[300px]">
              <SectionHeading
                heading="Always Up-to-Date"
                chipTitle="Web Search"
                smallHeading
                subheading="Most AI models have a knowledge cutoff, but GAIA can fetch real-time updates from the internet. Whether it's breaking news or the latest industry trends, you'll always have access to the most up-to-date insights."
                icon={
                  <GlobalSearchIcon
                    className="size-[35px] sm:size-[35px]"
                    color="#9b9b9b"
                  />
                }
              />
              <div className="space-y-2 px-7 py-0 sm:p-6 sm:px-6">
                <div className="flex items-start gap-2">
                  <CheckmarkCircle02Icon
                    width={25}
                    height={25}
                    color="#00bbff"
                  />
                  Real-time answers, never outdated.
                </div>
                <div className="flex items-start gap-2">
                  <CheckmarkCircle02Icon
                    width={25}
                    height={25}
                    color="#00bbff"
                  />
                  Instant fact-checking from live sources.
                </div>
                <div className="flex items-start gap-2">
                  <CheckmarkCircle02Icon
                    width={25}
                    height={25}
                    color="#00bbff"
                  />
                  Goes beyond preloaded AI knowledge.
                </div>
              </div>
            </div>

            <ImageCarousel images={webSearchImages} />
          </div>

          <div className="flex h-full w-full flex-col items-center justify-between gap-5 rounded-3xl bg-zinc-900 p-0 pb-10 sm:gap-0 sm:p-7 sm:pb-7">
            <div className="min-h-[300px]">
              <SectionHeading
                heading="Let AI Read for You"
                chipTitle="Fetch Webpages"
                smallHeading
                subheading="Ever wished your AI assistant could read and understand content from webpages? GAIA fetches and processes web content, so you get instant insights without endless scrolling."
                icon={
                  <InternetIcon
                    className="size-[35px] sm:size-[35px]"
                    color="#9b9b9b"
                  />
                }
              />
              <div className="space-y-2 px-7 py-0 pb-6 sm:p-6 sm:px-6">
                <div className="flex items-start gap-2">
                  <CheckmarkCircle02Icon
                    width={25}
                    height={25}
                    color="#00bbff"
                  />
                  Instantly fetch and summarize any webpage.
                </div>
                <div className="flex items-start gap-2">
                  <CheckmarkCircle02Icon
                    width={25}
                    height={25}
                    color="#00bbff"
                  />
                  No more searching through clutter—get key insights fast.
                </div>
                <div className="flex items-start gap-2">
                  <CheckmarkCircle02Icon
                    width={25}
                    height={25}
                    color="#00bbff"
                  />
                  Works on articles, research papers, blogs, and more.
                </div>
              </div>
            </div>

            <ImageCarousel images={fetchWebpageImages} />
          </div>
        </div>
      </div>
    </div>
  );
}

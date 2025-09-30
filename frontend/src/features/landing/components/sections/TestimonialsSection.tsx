import { Marquee } from "@/components/ui/marquee";
import { cn } from "@/lib/utils";

import { testimonials } from "../../data/testimonials";
import LargeHeader from "../shared/LargeHeader";
import SectionLayout from "../shared/SectionLayout";
import Image from "next/image";

const firstRow = testimonials.slice(0, testimonials.length / 2);
const secondRow = testimonials.slice(testimonials.length / 2);

const TestimonialCard = ({
  img,
  name,
  body,
  role,
}: {
  img: string;
  name: string;
  body: string;
  role: string;
}) => {
  return (
    <figure
      className={cn(
        "relative h-full w-100 overflow-hidden rounded-2xl border p-4 transition-all",
        "border-zinc-950 bg-zinc-900 hover:bg-zinc-800",
      )}
    >
      <div className="flex flex-row items-center gap-3">
        <Image
          className="rounded-full bg-white"
          width="35"
          height="35"
          alt={`${name} avatar`}
          src={img}
        />
        <div className="flex flex-col">
          <figcaption className="text-sm font-medium text-white">
            {name}
          </figcaption>
          <p className="text-xs text-zinc-500">{role}</p>
        </div>
      </div>
      <blockquote className="mt-3 text-sm leading-relaxed text-white/80">
        "{body}"
      </blockquote>
    </figure>
  );
};

export default function TestimonialsSection() {
  return (
    <SectionLayout className="flex h-screen items-center py-20">
      <div className="flex w-full max-w-7xl flex-col items-center justify-center">
        <LargeHeader
          chipText="Wall of Love"
          headingText="Loved by thousands of users"
          subHeadingText="See what people are saying about their experience with GAIA"
          centered
        />

        <div className="relative mt-16 flex w-full flex-col items-center justify-center overflow-hidden">
          <Marquee pauseOnHover className="[--duration:30s]">
            {firstRow.map((testimonial) => (
              <TestimonialCard key={testimonial.name} {...testimonial} />
            ))}
          </Marquee>
          <Marquee reverse pauseOnHover className="[--duration:35s]">
            {secondRow.map((testimonial) => (
              <TestimonialCard key={testimonial.name} {...testimonial} />
            ))}
          </Marquee>

          {/* Gradient overlays */}
          <div className="pointer-events-none absolute inset-y-0 left-0 w-1/6 bg-gradient-to-r from-background to-transparent" />
          <div className="pointer-events-none absolute inset-y-0 right-0 w-1/6 bg-gradient-to-l from-background to-transparent" />
        </div>
      </div>
    </SectionLayout>
  );
}

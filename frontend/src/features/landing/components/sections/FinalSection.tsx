import Image from "next/image";

import GetStartedButton from "../shared/GetStartedButton";
import { SplitTextBlur } from "../hero/SplitTextBlur";
import { MotionContainer } from "@/layouts/MotionContainer";
export default function FinalSection() {
  return (
    <div className="relative z-1 m-0! flex min-h-[90vh] w-screen flex-col items-center justify-center gap-4 overflow-hidden">
      <div className="absolute inset-0 h-full w-full">
        <Image
          src="/images/wallpapers/surreal.webp"
          alt="Wallpaper"
          fill
          sizes="100vw"
          className="noisy object-cover opacity-85"
          priority
        />
        <div className="pointer-events-none absolute inset-x-0 top-0 z-10 h-[30vh] bg-gradient-to-b from-black via-black/50 to-transparent" />
        <div className="pointer-events-none absolute inset-x-0 bottom-0 z-10 h-[30vh] bg-gradient-to-t from-black to-transparent" />
      </div>

      <MotionContainer className="relative z-2 mb-30 flex h-full flex-col items-center justify-start gap-4">
        <SplitTextBlur
          text="Your Life, Supercharged by GAIA"
          delay={0}
          className="z-[10] max-w-(--breakpoint-xl) text-center text-[2.8rem] leading-none font-medium tracking-tighter sm:text-[5rem]"
        />
        <div className="z-[1] mb-6 max-w-(--breakpoint-sm) px-4 py-0 text-center text-lg leading-7 font-light tracking-tighter text-foreground-700 sm:px-0 sm:text-xl">
          Join thousands already upgrading their productivity.
        </div>
        <GetStartedButton />
      </MotionContainer>
    </div>
    // </div>
  );
}

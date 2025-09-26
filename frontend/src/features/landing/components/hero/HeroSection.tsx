import Link from "next/link";

import ShinyText from "@/components/ui/shadcn/shimmering-chip";
import { useLatestRelease } from "@/hooks/useLatestRelease";
import { MotionContainer } from "@/layouts/MotionContainer";

import GetStartedButton from "../shared/GetStartedButton";
import { SplitTextBlur } from "./SplitTextBlur";

export default function HeroSection() {
  const { data: release, isLoading: isReleaseLoading } =
    useLatestRelease("heygaia/gaia");

  return (
    <div className="relative mt-28 w-screen flex-col gap-8 py-16 sm:pb-10">
      {/* <div className="particles absolute top-0 z-1 h-screen w-full overflow-hidden bg-[#00bbff50] bg-[radial-gradient(circle_at_center,_#00bbff50_0%,_#00bbff50_40%,_#01bbff0d_75%,_transparent_100%)]">

        <div className="vignette absolute h-[351%] w-full bg-[radial-gradient(circle,_rgba(0,0,0,0)_0%,_rgba(0,0,0,0)_47%,_#000_80%)]" />
      </div> */}

      <MotionContainer className="relative z-2 flex h-full flex-col items-center justify-start gap-4">
        <Link href="/blog/public-beta">
          <ShinyText
            text={`Public Beta ${isReleaseLoading ? "" : release?.name.replace("-beta", "")}`}
            speed={10}
            className="relative z-10 cursor-pointer rounded-full bg-zinc-900 p-1 px-4 text-sm font-light outline-1 outline-zinc-800 transition-colors hover:bg-zinc-800"
          />
        </Link>

        <SplitTextBlur
          text="Meet the personal assistant you’ve always wanted"
          delay={0}
          className="z-[10] max-w-(--breakpoint-lg) text-center text-[2.8rem] leading-none font-medium tracking-tighter sm:text-[5rem]"
        />
        <div className="mb-6 max-w-(--breakpoint-sm) px-4 py-0 text-center text-lg leading-7 font-light tracking-tighter text-foreground-700 sm:px-0 sm:text-xl">
          Tired of Siri, Google Assistant, and ChatGPT doing nothing useful?
        </div>
        <GetStartedButton small_text />
      </MotionContainer>
    </div>
  );
}

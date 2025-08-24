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
    <div className="mt-28 w-screen flex-col gap-8 py-16 sm:pb-10">
      <div className="particles absolute top-0 z-1 h-screen w-full overflow-hidden bg-[#01bbff1a] bg-[radial-gradient(circle_at_center,_#01bbff40_0%,_#01bbff26_40%,_#01bbff0d_75%,_transparent_100%)]">
        <div className="vignette absolute h-[351%] w-full bg-[radial-gradient(circle,_rgba(0,0,0,0)_0%,_rgba(0,0,0,0)_47%,_rgba(0,0,0,1)_80%)]" />
      </div>

      <MotionContainer className="relative z-2 flex h-full flex-col items-center justify-start gap-4">
        <Link href="/blog/public-beta">
          <ShinyText
            text={`Public Beta ${isReleaseLoading ? "" : release?.name.replace("-beta", "")}`}
            speed={10}
            className="relative z-10 cursor-pointer rounded-full bg-zinc-900 p-2 px-4 text-sm font-light outline-1 outline-zinc-800 transition-colors hover:bg-zinc-800"
          />
        </Link>

        <SplitTextBlur
          text="Meet the personal assistant you’ve always wanted"
          className="max-w-(--breakpoint-lg) text-center text-[2.8rem] font-medium text-white sm:text-7xl"
        />
        <div className="mb-6 max-w-(--breakpoint-sm) px-4 py-0 text-center text-lg leading-7 font-light text-foreground-500 sm:px-0 sm:text-lg">
          Tired of Siri, Google Assistant, and ChatGPT doing nothing useful?
        </div>
        <GetStartedButton />
      </MotionContainer>
    </div>
  );
}

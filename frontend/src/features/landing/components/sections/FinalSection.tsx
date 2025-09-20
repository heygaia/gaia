import Image from "next/image";

import GetStartedButton from "../shared/GetStartedButton";
export default function FinalSection() {
  return (
    <div className="relative z-1 m-0! flex min-h-[80vh] w-screen flex-col items-center justify-center overflow-hidden pb-20 sm:min-h-fit">
      <div className="relative flex w-full max-w-7xl flex-col items-center justify-center gap-6 overflow-hidden rounded-4xl bg-gradient-to-b from-zinc-900 to-zinc-950 outline-1 outline-zinc-900 sm:p-28 sm:py-20">
        <div className="absolute inset-0 z-[2] flex h-full w-full scale-150 justify-start overflow-hidden">
          <Image
            src="/images/logos/logo.webp"
            alt="GAIA Logo"
            className="h-full object-contain opacity-[7%] grayscale"
            fill
          />
        </div>

        <div className="relative z-10 text-center text-4xl font-medium sm:text-6xl">
          Your Life, Supercharged by GAIA
        </div>
        <div className="relative z-10 max-w-(--breakpoint-md) text-center text-lg font-light text-foreground-500">
          Join thousands already upgrading their productivity.
        </div>

        <div className="relative z-10">
          <GetStartedButton text="Sign Up" />
        </div>
      </div>
    </div>
  );
}

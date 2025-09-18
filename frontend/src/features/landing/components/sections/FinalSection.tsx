import Image from "next/image";

import GetStartedButton from "../shared/GetStartedButton";

export default function FinalSection() {
  return (
    <div className="relative z-1 m-0! flex min-h-[80vh] w-screen flex-col items-center justify-center overflow-hidden bg-[radial-gradient(ellipse_at_top_left,_rgba(15,15,15,0.9),_rgba(9,9,11,1)),linear-gradient(to_bottom,_#0c0c0c,_#0a0a0a)] bg-cover bg-fixed bg-no-repeat p-5 sm:min-h-fit">
      <div className="absolute inset-0 bg-[radial-gradient(circle_at_50%_50%,rgba(1,187,255,0.03),transparent_50%)]" />
      <div className="absolute inset-0 bg-[linear-gradient(to_right,#80808008_1px,transparent_1px),linear-gradient(to_bottom,#80808008_1px,transparent_1px)] bg-[size:32px_32px]" />

      <div className="relative my-20 flex w-full max-w-7xl flex-col items-center justify-center gap-6 overflow-hidden rounded-4xl bg-gradient-to-b from-zinc-900 via-zinc-950 to-black outline-1 outline-zinc-800 sm:p-28">
        <div className="absolute inset-0 z-[2] flex h-full w-full scale-150 justify-start overflow-hidden">
          <Image
            src="/branding/logo.webp"
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
          <GetStartedButton small_text text="Sign Up" />
        </div>
      </div>
    </div>
  );
}

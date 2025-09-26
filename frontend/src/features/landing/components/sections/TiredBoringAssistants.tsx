import Image from "next/image";

import GetStartedButton from "../shared/GetStartedButton";
import LargeHeader from "../shared/LargeHeader";

export default function Tired() {
  return (
    <div className="relative flex h-screen flex-col items-center justify-center gap-2 p-10">
      <div
        className="absolute inset-0 z-0 h-[90%]"
        style={{
          backgroundImage: `
          radial-gradient(circle at 50% 100%, rgba(0, 187, 255, 0.1) 0%, transparent 60%),
          radial-gradient(circle at 50% 100%, rgba(255, 255, 255, 0.1) 0%, transparent 70%),
          radial-gradient(circle at 50% 100%, rgba(0, 187, 255, 0.3) 0%, transparent 70%)
        `,
        }}
      />
      <LargeHeader
        headingText="Tired of Boring Assistants?"
        subHeadingText="Meet one that actually works."
        centered
      />

      <div className="relative z-[1] flex gap-14 pt-10">
        <Image
          src={
            "/images/icons/siri.webp"
          }
          alt="Siri Logo"
          width={70}
          height={70}
          className="size-[65px] translate-y-7 -rotate-8 rounded-2xl"
        />

        <Image
          src={
            "https://static.vecteezy.com/system/resources/previews/055/687/055/non_2x/rectangle-gemini-google-icon-symbol-logo-free-png.png"
          }
          alt="Gemini Logo"
          width={70}
          height={70}
          className="object-fit size-[80px] rounded-2xl"
        />

        <Image
          src={
            "https://static.vecteezy.com/system/resources/previews/024/558/807/non_2x/openai-chatgpt-logo-icon-free-png.png"
          }
          alt="ChatGPT Logo"
          width={70}
          height={70}
          className="size-[65px] translate-y-7 rotate-8 rounded-2xl"
        />
      </div>

      <Image
        src={"/images/logos/logo.webp"}
        alt="GAIA Logo"
        width={120}
        height={120}
        className="relative z-[1] my-14 rounded-3xl bg-gradient-to-b from-zinc-800 to-zinc-950 p-4 shadow-[0px_0px_100px_40px_rgba(0,_187,_255,_0.2)] outline-1 outline-zinc-800"
      />

      <div className="absolute bottom-32 z-[1] flex w-full max-w-lg items-center">
        <div className="absolute bottom-16 left-0 -rotate-12 rounded-xl bg-zinc-800 px-3 py-2 text-sm text-zinc-500">
          Personalised
        </div>

        <div className="absolute right-0 bottom-16 rotate-12 rounded-xl bg-zinc-800 px-3 py-2 text-sm text-zinc-500">
          Proactive
        </div>

        <div className="absolute bottom-40 left-10 rotate-12 rounded-xl bg-zinc-800 px-3 py-2 text-sm text-zinc-500">
          Automated
        </div>

        <div className="absolute right-10 bottom-40 -rotate-12 rounded-xl bg-zinc-800 px-3 py-2 text-sm text-zinc-500">
          Integrated
        </div>
      </div>

      <GetStartedButton text="See GAIA in Action" />
    </div>
  );
}

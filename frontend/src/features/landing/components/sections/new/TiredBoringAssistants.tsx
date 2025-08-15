import Image from "next/image";

export default function Tired() {
  return (
    <div className="flex h-screen flex-col items-center justify-center gap-2 p-10">
      <div className="text-5xl font-medium">Tired of Boring Assistants?</div>
      <div className="text-2xl font-light text-foreground-400">
        Meet one that actually works.
      </div>

      <div className="flex gap-20 pt-10">
        <Image
          src={
            "https://upload.wikimedia.org/wikipedia/commons/thumb/d/de/Logo_Apple_Siri_iOS_2024.svg/1200px-Logo_Apple_Siri_iOS_2024.svg.png"
          }
          alt="Siri Logo"
          width={70}
          height={70}
          className="translate-y-5 -rotate-6 rounded-2xl"
        />

        <Image
          src={
            "https://static.vecteezy.com/system/resources/previews/055/687/055/non_2x/rectangle-gemini-google-icon-symbol-logo-free-png.png"
          }
          alt="Gemini Logo"
          width={70}
          height={70}
          className="object-fit rounded-2xl"
        />

        <Image
          src={
            "https://static.vecteezy.com/system/resources/previews/024/558/807/non_2x/openai-chatgpt-logo-icon-free-png.png"
          }
          alt="ChatGPT Logo"
          width={70}
          height={70}
          className="translate-y-5 rotate-6 rounded-2xl"
        />
      </div>

      <Image
        src={"/branding/logo.webp"}
        alt="GAIA Logo"
        width={120}
        height={120}
        className="mt-14 rounded-3xl bg-gradient-to-b from-zinc-800 to-zinc-950 p-4 shadow-[0px_0px_100px_40px_rgba(0,_187,_255,_0.2)] outline-1 outline-zinc-800"
      />
    </div>
  );
}

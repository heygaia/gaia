import { Tooltip } from "@heroui/tooltip";
import Image from "next/image";
import Link from "next/link";

import {
  DiscordIcon,
  Github,
  TwitterIcon,
  WhatsappIcon,
} from "@/components/shared/icons";

import { SplitTextBlur } from "../hero/SplitTextBlur";
import GetStartedButton from "../shared/GetStartedButton";

export const SOCIAL_LINKS = [
  {
    href: "https://twitter.com/_heygaia",
    ariaLabel: "Twitter Link",
    buttonProps: {
      color: "#1DA1F2",
      className: "rounded-xl text-black!",
      "aria-label": "Twitter Link Button",
    },
    icon: <TwitterIcon width={20} height={20} />,
    label: "Twitter",
  },
  {
    href: "https://whatsapp.heygaia.io",
    ariaLabel: "WhatsApp Link",
    buttonProps: {
      color: "#25D366",
      className: "rounded-xl text-black!",
      "aria-label": "WhatsApp Link Button",
    },
    icon: <WhatsappIcon width={20} height={20} />,
    label: "WhatsApp",
  },
  {
    href: "https://discord.heygaia.io",
    ariaLabel: "Discord Link",
    buttonProps: {
      color: "#5865f2",
      className: "rounded-xl text-black!",
      "aria-label": "Discord Link Button",
    },
    icon: <DiscordIcon width={20} height={20} />,
    label: "Discord",
  },
  {
    href: "https://github.com/heygaia/gaia",
    ariaLabel: "GitHub Link",
    buttonProps: {
      color: "#a6a6a6",
      className: "rounded-xl text-black!",
      "aria-label": "GitHub Link Button",
    },
    icon: <Github width={20} height={20} />,
    label: "GitHub",
  },
];

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

      <div className="relative z-2 mb-30 flex h-full flex-col items-center justify-start gap-4">
        <SplitTextBlur
          text="Your Life, Supercharged by GAIA"
          delay={0}
          className="z-[10] max-w-(--breakpoint-xl) text-center text-[2.8rem] leading-none font-medium tracking-tighter sm:text-[5rem]"
        />

        <div className="z-[1] mb-6 max-w-(--breakpoint-sm) px-4 py-0 text-center text-lg leading-7 font-light tracking-tighter text-foreground-600 sm:px-0 sm:text-xl">
          Join thousands already upgrading their productivity.
        </div>
        <GetStartedButton />

        <div className="mt-6 flex items-center gap-2">
          {SOCIAL_LINKS.map(
            ({ href, ariaLabel, buttonProps, icon, label }, index) => {
              const color = `hover:text-[${buttonProps.color}]`;
              return (
                <Tooltip content={label} placement="bottom" key={index + href}>
                  <Link
                    href={href}
                    aria-label={ariaLabel}
                    className={`flex w-10 scale-125 justify-center p-1 transition hover:scale-150 ${color}`}
                  >
                    {icon}
                  </Link>
                </Tooltip>
              );
            },
          )}
        </div>
      </div>
    </div>
  );
}

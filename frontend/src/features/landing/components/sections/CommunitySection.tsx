import Link from "next/link";

import { DiscordIcon, Github, TwitterIcon, WhatsappIcon } from "@/components";
import { RaisedButton } from "@/components/ui/shadcn/raised-button";

export default function CommunitySection() {
  return (
    <div className="flex h-[50vh] flex-col items-center justify-center gap-3 p-20">
      <div className="relative z-10 text-center text-4xl font-medium sm:text-6xl">
        Join our Community
      </div>
      <div className="relative z-10 max-w-(--breakpoint-md) text-center text-4xl font-light text-foreground-400 sm:text-3xl">
        Connect with others and stay in the loop
      </div>

      <div className="mt-2 flex items-center gap-2">
        <Link
          href={"https://https://twitter.com/_heygaia"}
          aria-label="Twitter Link"
        >
          <RaisedButton
            color="#1DA1F2"
            className="rounded-xl text-black!"
            size={"icon"}
            aria-label="Twitter Link Button"
          >
            <TwitterIcon width={20} height={20} />
          </RaisedButton>
        </Link>
        <Link href={"https://whatsapp.heygaia.io"} aria-label="WhatsApp Link">
          <RaisedButton
            color="#25D366"
            className="rounded-xl text-black!"
            size={"icon"}
            aria-label="WhatsApp Link Button"
          >
            <WhatsappIcon width={20} height={20} />
          </RaisedButton>
        </Link>
        <Link href={"https://discord.heygaia.io"} aria-label="Discord Link">
          <RaisedButton
            color="#5865f2"
            className="rounded-xl text-black!"
            aria-label="Discord Link Button"
            size={"icon"}
          >
            <DiscordIcon width={20} height={20} />
          </RaisedButton>
        </Link>
        <Link href={"https://github.com/heygaia/gaia"} aria-label="GitHub Link">
          <RaisedButton
            className="rounded-xl text-black! before:rounded-xl hover:scale-110"
            color="#a6a6a6"
            aria-label="GitHub Link Button"
            size={"icon"}
          >
            <Github width={20} height={20} />
          </RaisedButton>
        </Link>
      </div>
    </div>
  );
}

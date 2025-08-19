import { StarFilledIcon } from "@radix-ui/react-icons";
import { ArrowRight } from "lucide-react";
import Image from "next/image";
import Link from "next/link";

import { RaisedButton } from "@/components/ui/shadcn/raised-button";

import LargeHeader from "../../shared/LargeHeader";

export default function OpenSource() {
  return (
    <>
      <div className="flex flex-col items-center justify-center gap-10">
        <div className="flex w-full max-w-7xl flex-col items-center justify-center rounded-4xl bg-gradient-to-b from-zinc-900 to-zinc-950 p-10 outline-1 outline-zinc-900">
          <LargeHeader
            headingText="Open-Source & Self-Hostable"
            subHeadingText="GAIA is fully open source. Self-host it on your own infrastructure, or explore the community-driven codebase on GitHub!"
            centered
          />
          <div className="flex -space-x-16">
            <Image
              src={"/icons/docker3d.png"}
              alt="Docker Logo"
              width={200}
              height={200}
              className="relative z-[1] -rotate-10"
            />
            <Image
              src={"/icons/github3d.png"}
              alt="Docker Logo"
              width={200}
              className="relative z-[2] rotate-3"
              height={200}
            />
          </div>
          <div className="flex gap-3 pt-10">
            <Link href={"https://docs.heygaia.io"}>
              <RaisedButton
                className="rounded-xl text-white! before:rounded-xl hover:scale-110"
                color="#292929"
              >
                Read Docs
                <ArrowRight width={15} />
              </RaisedButton>
            </Link>
            <Link href={"https://github.com/heygaia/gaia"}>
              <RaisedButton
                className="rounded-xl text-black! before:rounded-xl hover:scale-110"
                color="#00bbff"
              >
                Star on GitHub <StarFilledIcon width={17} height={17} />
              </RaisedButton>
            </Link>
          </div>
        </div>
      </div>
    </>
  );
}

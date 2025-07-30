"use client";

import Link from "next/link";

import { ChatBubbleAddIcon, Target02Icon } from "@/components/shared/icons";
import { Button } from "@/components/ui/shadcn/button";

import HeaderComponent from "./HeaderComponent";

export default function GoalsHeader() {
  return (
    <>
      <HeaderComponent title="Goals" icon={<Target02Icon />} />
      <div className="flex gap-2">
        <Link href={"/c"}>
          <Button
            aria-label="Create new chat"
            className={`group rounded-lg hover:bg-[#00bbff]/20`}
            size="icon"
            variant={"ghost"}
          >
            <ChatBubbleAddIcon className="text-zinc-400 transition-all group-hover:text-primary" />
          </Button>
        </Link>
      </div>
    </>
  );
}

"use client";

import { Search } from "lucide-react";
import Link from "next/link";
import { useState } from "react";

import { SidebarHeaderButton } from "@/components";
import { ChatBubbleAddIcon, PinIcon } from "@/components/shared/icons";
import ModelPickerButton from "@/features/chat/components/composer/ModelPickerButton";
import { NotificationCenter } from "@/features/notification/components/NotificationCenter";
import SearchCommand from "@/features/search/components/SearchCommand";

export default function ChatHeader() {
  const [openSearchDialog, setOpenSearchDialog] = useState(false);

  return (
    <div className="flex w-full justify-between">
      <ModelPickerButton />
      <div className="relative z-[100] flex items-center">
        {/* <div
          className="absolute -right-2 h-full w-[130%] bg-red-500"
          style={{
            clipPath: `polygon(
            0 0,
            100% 0,
            100% 100%,
            38% calc(100%-2px)
          )`,
          }}
        ></div>
           */}
        <SearchCommand
          openSearchDialog={openSearchDialog}
          setOpenSearchDialog={setOpenSearchDialog}
        />
        <SidebarHeaderButton
          onClick={() => setOpenSearchDialog(true)}
          aria-label="Search"
          tooltip="Search"
        >
          <Search className="max-h-5 min-h-5 max-w-5 min-w-5 text-zinc-400 group-hover:text-primary" />
        </SidebarHeaderButton>
        <Link href={"/pins"}>
          <SidebarHeaderButton
            aria-label="Pinned Messages"
            tooltip="Pinned Messages"
          >
            <PinIcon className="min-h-[20px] min-w-[20px] text-zinc-400 transition-all group-hover:text-primary" />
          </SidebarHeaderButton>
        </Link>
        <Link href={"/c"}>
          <SidebarHeaderButton
            aria-label="Create new chat"
            tooltip="Create new chat"
          >
            <ChatBubbleAddIcon className="min-h-[20px] min-w-[20px] text-zinc-400 transition-all group-hover:text-primary" />
          </SidebarHeaderButton>
        </Link>
        <NotificationCenter />
      </div>
    </div>
  );
}

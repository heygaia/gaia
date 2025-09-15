"use client";

import { Search } from "lucide-react";
import Link from "next/link";
import { useParams } from "next/navigation";
import { useState } from "react";

import { SidebarHeaderButton } from "@/components";
import ChatOptionsDropdown from "@/components/layout/sidebar/ChatOptionsDropdown";
import {
  BubbleConversationChatIcon,
  ChatBubbleAddIcon,
  PinIcon,
} from "@/components/shared/icons";
import { useConversationList } from "@/features/chat/hooks/useConversationList";
import { NotificationCenter } from "@/features/notification/components/NotificationCenter";
import SearchCommand from "@/features/search/components/SearchCommand";

export default function ChatHeader() {
  const { conversations } = useConversationList();
  const { id: convoIdParam } = useParams<{ id: string }>();
  const [openSearchDialog, setOpenSearchDialog] = useState(false);

  return (
    <div className="flex w-full justify-between pb-3">
      <div />
      <div className="flex">
        {convoIdParam && (
          <ChatOptionsDropdown
            btnChildren={
              <div className="flex max-w-[250px] items-center gap-2 truncate text-sm!">
                <BubbleConversationChatIcon height={18} width={18} />

                {conversations.find(
                  (convo) => convo.conversation_id == convoIdParam,
                )?.description || "New chat"}
              </div>
            }
            buttonHovered={true}
            chatId={convoIdParam}
            chatName={
              conversations.find(
                (convo) => convo.conversation_id == convoIdParam,
              )?.description || "New chat"
            }
            logo2={true}
            starred={
              conversations.find(
                (convo) => convo.conversation_id == convoIdParam,
              )?.starred || false
            }
          />
        )}
      </div>
      <div className="z-[100] flex">
        <SearchCommand
          openSearchDialog={openSearchDialog}
          setOpenSearchDialog={setOpenSearchDialog}
        />

        <SidebarHeaderButton
          onClick={() => setOpenSearchDialog(true)}
          aria-label="Search"
        >
          <Search className="max-h-5 min-h-5 max-w-5 min-w-5 text-zinc-400 group-hover:text-primary" />
        </SidebarHeaderButton>

        <Link href={"/pins"}>
          <SidebarHeaderButton aria-label="Pinned Messages">
            <PinIcon className="min-h-[20px] min-w-[20px] text-zinc-400 transition-all group-hover:text-primary" />
          </SidebarHeaderButton>
        </Link>

        <Link href={"/c"}>
          <SidebarHeaderButton aria-label="Create new chat">
            <ChatBubbleAddIcon className="min-h-[20px] min-w-[20px] text-zinc-400 transition-all group-hover:text-primary" />
          </SidebarHeaderButton>
        </Link>

        <NotificationCenter />
      </div>
    </div>
  );
}

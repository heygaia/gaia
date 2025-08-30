"use client";
import { BotIcon, Star, Zap } from "lucide-react";
import { usePathname, useRouter } from "next/navigation";
import { FC, useEffect, useState } from "react";

import {
  BubbleConversationChatIcon,
  Mail01Icon,
} from "@/components/shared/icons";
import { SystemPurpose } from "@/features/chat/api/chatApi";

import { Button } from "../../ui/shadcn/button";
import ChatOptionsDropdown from "./ChatOptionsDropdown";

interface ChatTabProps {
  name: string;
  id: string;
  starred: boolean | undefined;
  isSystemGenerated?: boolean;
  systemPurpose?: SystemPurpose;
}

export const ChatTab: FC<ChatTabProps> = ({
  name,
  id,
  starred,
  isSystemGenerated = false,
  systemPurpose,
}) => {
  const router = useRouter();
  const [currentConvoId, setCurrentConvoId] = useState<string | null>(null);
  const pathname = usePathname();
  const [buttonHovered, setButtonHovered] = useState(false);

  useEffect(() => {
    const pathParts = location.pathname.split("/");

    setCurrentConvoId(pathParts[pathParts.length - 1]);
  }, [pathname]);

  return (
    <div
      className="relative z-0 flex"
      onMouseOut={() => setButtonHovered(false)}
      onMouseOver={() => setButtonHovered(true)}
    >
      <Button
        className={`flex h-[32px] min-h-[32px] w-full cursor-pointer justify-start bg-transparent pr-0 pl-2 font-normal duration-0 hover:bg-white/10 ${
          currentConvoId === id ? "text-primary" : "text-white"
        }`}
        onClick={() => {
          setButtonHovered(false);
          router.push(`/c/${id}`);
        }}
      >
        <div className="flex w-full items-center gap-2">
          {isSystemGenerated ? (
            <div className="flex w-[17px] min-w-[17px] items-center justify-center">
              <span className="text-xs">
                {systemPurpose === SystemPurpose.EMAIL_PROCESSING ? (
                  <Mail01Icon
                    color={currentConvoId === id ? "#00bbff" : "#9b9b9b"}
                    width="19"
                  />
                ) : systemPurpose === SystemPurpose.WORKFLOW_EXECUTION ? (
                  <Zap
                    color={currentConvoId === id ? "#00bbff" : "#9b9b9b"}
                    width="19"
                  />
                ) : (
                  <BotIcon
                    color={currentConvoId === id ? "#00bbff" : "#9b9b9b"}
                    width="19"
                  />
                )}
              </span>
            </div>
          ) : starred ? (
            <Star
              className="w-[17px] min-w-[17px]"
              color={currentConvoId === id ? "#00bbff" : "#9b9b9b"}
              width="19"
            />
          ) : (
            <BubbleConversationChatIcon
              className="w-[17px] min-w-[17px]"
              color={currentConvoId === id ? "#00bbff" : "#9b9b9b"}
              width="19"
            />
          )}
          <span
            className={`w-[calc(100%-45px)] max-w-[200px] truncate text-left`}
          >
            {name.replace('"', "")}
          </span>
        </div>
      </Button>

      <div
        className={`absolute right-0 ${
          buttonHovered ? "bg-black/20 backdrop-blur-md" : "bg-transparent"
        } rounded-full`}
      >
        <ChatOptionsDropdown
          buttonHovered={buttonHovered}
          chatId={id}
          chatName={name}
          starred={starred}
        />
      </div>
    </div>
  );
};

"use client";
import { Button } from "@heroui/button";
import { BotIcon, Star, Zap } from "lucide-react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import React, { FC, useEffect, useState } from "react";

import {
  BubbleConversationChatIcon,
  Mail01Icon,
} from "@/components/shared/icons";
import { SystemPurpose } from "@/features/chat/api/chatApi";

import ChatOptionsDropdown from "./ChatOptionsDropdown";

const ICON_WIDTH = "19";
const ICON_SIZE = "w-[17px] min-w-[17px]";
const ACTIVE_COLOR = "#00bbff";
const INACTIVE_COLOR = "#9b9b9b";

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
  const [currentConvoId, setCurrentConvoId] = useState<string | null>(null);
  const pathname = usePathname();
  const [buttonHovered, setButtonHovered] = useState(false);

  useEffect(() => {
    const pathParts = location.pathname.split("/");
    setCurrentConvoId(pathParts[pathParts.length - 1]);
  }, [pathname]);

  const isActive = currentConvoId === id;
  const iconColor = isActive ? ACTIVE_COLOR : INACTIVE_COLOR;

  const getIcon = () => {
    const iconProps = { color: iconColor, width: ICON_WIDTH };

    if (isSystemGenerated) {
      if (systemPurpose === SystemPurpose.EMAIL_PROCESSING)
        return <Mail01Icon {...iconProps} />;

      if (systemPurpose === SystemPurpose.WORKFLOW_EXECUTION)
        return <Zap {...iconProps} />;

      return <BotIcon {...iconProps} />;
    }

    if (starred) return <Star className={ICON_SIZE} {...iconProps} />;

    return <BubbleConversationChatIcon className={ICON_SIZE} {...iconProps} />;
  };

  return (
    <div
      className="relative z-0 flex"
      onMouseOut={() => setButtonHovered(false)}
      onMouseOver={() => setButtonHovered(true)}
    >
      <Button
        className={`w-full justify-start text-sm ${
          isActive ? "text-primary" : "text-zinc-400"
        }`}
        size="sm"
        as={Link}
        href={`/c/${id}`}
        variant="light"
        color={isActive ? "primary" : "default"}
        onPress={() => setButtonHovered(false)}
        startContent={React.cloneElement(getIcon(), {
          width: 18,
          height: 18,
        })}
      >
        {name.replace('"', "")}
      </Button>

      <div className={`absolute right-0`}>
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
